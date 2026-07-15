import os
import threading
import time
import argparse
import asyncio
import shutil
from tqdm import tqdm
from datetime import datetime
from config import load_config
from handlers import get_handler_for_extension
from utils.cleanup import purge_uploads, check_uploads_dir
from utils.chunking import audit_files, chunk_files_by_size, process_chunks


class CLIRenderer:
    def __init__(self, config):
        self.config = config
        self.upload_folder = config.get("UPLOAD_FOLDER", "/tmp/rmeta_uploads")
        self.session_timeout = config.get("SESSION_TIMEOUT", 600)

    def start_auto_cleanup(self, interval_override=None):
        interval = interval_override if interval_override is not None else self.config.get("AUTO_CLEAN_INTERVAL", 600)
        upload_folder = self.upload_folder
        def auto_cleanup_loop():
            while True:
                time.sleep(interval)
                try:
                    purge_uploads(upload_folder)
                    print(f"[Auto-cleanup] Purged {upload_folder}")
                except Exception as e:
                    print(f"[Auto-cleanup] Error: {e}")
        t = threading.Thread(target=auto_cleanup_loop, daemon=True)
        t.start()

    def run(self):
        parser = argparse.ArgumentParser(description="rMeta CLI - Metadata extraction tool")
        parser.add_argument('-f', '--files', nargs='+', help='Files to process (upload and process)')
        parser.add_argument('-d', '--dir', type=str, help='Directory to process (upload and process)')
        parser.add_argument('--r', action='store_true', help='Recursively process files in directory')
        parser.add_argument('--filetype', type=str, help='Only process files of this type (e.g., pdf, docx)')
        parser.add_argument('--auto-clean-interval', type=int, help='Set auto-cleanup interval in seconds')
        parser.add_argument('--version', action='version', version='rMeta CLI v0.4.0')
        parser.add_argument('--config', type=str, help='Path to custom config file')
        parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
        parser.add_argument('--gpg-key', type=str, help='Encrypt processed files with this GPG public key')
        parser.add_argument('--sha256', action='store_true', help='Generate SHA256 hashfiles for processed files')
        parser.add_argument('--dry-run', action='store_true', help='Preview actions without modifying files')
        parser.add_argument('--clean-after', action='store_true', help='Securely delete session files after processing')

        subparsers = parser.add_subparsers(dest="command")
        download_parser = subparsers.add_parser("download", help="Download processed results")
        download_parser.add_argument("output", help="Output directory")
        cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup session files")

        args = parser.parse_args()
        self.start_auto_cleanup(interval_override=args.auto_clean_interval)

        if args.verbose:
            print("[VERBOSE] Arguments:", args)

        if args.files:
            uploaded = self.upload_files(args.files, recursive=False, filetype=args.filetype, verbose=args.verbose)
            self.process_files(
                files=uploaded, gpg_key=args.gpg_key, sha256=args.sha256,
                dry_run=args.dry_run, clean_after=args.clean_after,
                filetype=args.filetype, verbose=args.verbose,
            )
            if args.clean_after and not args.dry_run:
                print("Cleaning up session files...")
                purge_uploads(self.upload_folder)
            return
        elif args.dir:
            uploaded = self.upload_files([args.dir], recursive=args.r, filetype=args.filetype, verbose=args.verbose)
            self.process_files(
                files=uploaded, gpg_key=args.gpg_key, sha256=args.sha256,
                dry_run=args.dry_run, clean_after=args.clean_after,
                filetype=args.filetype, verbose=args.verbose,
            )
            if args.clean_after and not args.dry_run:
                print("Cleaning up session files...")
                purge_uploads(self.upload_folder)
            return

        if args.command == "download":
            self.download_results(args.output)
        elif args.command == "cleanup":
            self.cleanup()
        else:
            parser.print_help()

    def upload_files(self, files, recursive=False, filetype=None, verbose=False):
        print(f"Uploading files to {self.upload_folder}...")
        os.makedirs(self.upload_folder, exist_ok=True)
        uploaded = []
        def should_include(f):
            if filetype:
                types = [t.strip().lower() for t in filetype.split(',')]
                return any(f.lower().endswith(f'.{t}') for t in types)
            return True
        def upload_file(f):
            if os.path.isfile(f) and should_include(f):
                dest = os.path.join(self.upload_folder, os.path.basename(f))
                shutil.copy2(f, dest)
                uploaded.append(dest)
                if verbose:
                    print(f"  Uploaded: {f} -> {dest}")
            elif os.path.isdir(f):
                if recursive:
                    for root, _, files_in_dir in os.walk(f):
                        for file_in_dir in files_in_dir:
                            full_path = os.path.join(root, file_in_dir)
                            if should_include(full_path):
                                upload_file(full_path)
                else:
                    for file_in_dir in os.listdir(f):
                        full_path = os.path.join(f, file_in_dir)
                        if os.path.isfile(full_path) and should_include(full_path):
                            dest = os.path.join(self.upload_folder, os.path.basename(full_path))
                            shutil.copy2(full_path, dest)
                            uploaded.append(dest)
                            if verbose:
                                print(f"  Uploaded: {full_path} -> {dest}")
            else:
                if verbose:
                    print(f"  Skipped: {f}")
        for f in files:
            upload_file(f)
        return uploaded

    def process_files(self, files=None, gpg_key=None, sha256=False, dry_run=False, clean_after=False, filetype=None, verbose=False):
        print("Processing files...")
        if files is None:
            files = [os.path.join(self.upload_folder, f) for f in os.listdir(self.upload_folder) if os.path.isfile(os.path.join(self.upload_folder, f))]
            if filetype:
                files = [f for f in files if f.lower().endswith(f'.{filetype.lower()}')]
        if not files:
            print("No files to process.")
            return
        min_memory_mb = self.config.get("MIN_MEM_MB", 512)
        chunk_mb = self.config.get("MAX_HANDLER_TIMEOUT", 30)
        print(f"  Auditing {len(files)} files...")
        supported, too_large, skipped = audit_files(files, min_memory_mb)
        print(f"  Supported: {supported}")
        if too_large:
            print(f"  Too large: {too_large}")
        if skipped:
            print(f"  Skipped: {skipped}")
        log_path = os.path.join(self.upload_folder, "session_log.txt")
        def log_event(msg):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a") as logf:
                logf.write(f"[{ts}] {msg}\n")
        if dry_run:
            print("[DRY RUN] Would process the following files:")
            for file in supported:
                print(f"  - {file}")
                log_event(f"DRY RUN: Would process {file}")
            if sha256:
                print("[DRY RUN] Would generate SHA256 hashfiles for:")
                for file in supported:
                    print(f"  - {file}")
                    log_event(f"DRY RUN: Would generate SHA256 for {file}")
            if gpg_key:
                print(f"[DRY RUN] Would encrypt with GPG key: {gpg_key} for:")
                for file in supported:
                    print(f"  - {file}")
                    log_event(f"DRY RUN: Would encrypt {file} with GPG key {gpg_key}")
            print("[DRY RUN] No files were modified.")
            log_event("DRY RUN: No files were modified.")
            return

        results = []

        def scrub_chunk(file_list):
            for filepath in file_list:
                filename = os.path.basename(filepath)
                ext = os.path.splitext(filename)[1].lower().lstrip(".")
                handler_entry = get_handler_for_extension(ext)

                file_result = {"filename": filename, "scrubbed": False, "warnings": []}

                if not handler_entry:
                    file_result["warnings"].append("Unsupported file type")
                    results.append(file_result)
                    log_event(f"Skipped (unsupported type): {filepath}")
                    continue

                try:
                    scrub_fn = handler_entry.get("scrub")
                    get_additional_messages_fn = handler_entry.get("get_additional_messages")
                    is_async = handler_entry.get("is_async", False)
                    msgs_is_async = handler_entry.get("msgs_is_async", False)

                    if scrub_fn:
                        if is_async:
                            asyncio.run(scrub_fn(filepath))
                        else:
                            scrub_fn(filepath)
                        file_result["scrubbed"] = True

                    if get_additional_messages_fn:
                        if msgs_is_async:
                            extra = asyncio.run(get_additional_messages_fn(filepath))
                        else:
                            extra = get_additional_messages_fn(filepath)
                        file_result["warnings"].extend(extra)

                    log_event(f"Processed {filepath}")
                except Exception as e:
                    file_result["warnings"].append(f"Error: {e}")
                    log_event(f"Error processing {filepath}: {e}")

                results.append(file_result)

        chunks = chunk_files_by_size(supported, chunk_mb)
        print(f"  Processing {len(chunks)} chunks...")
        for chunk in tqdm(chunks, desc="Processing", unit="chunk"):
            process_chunks([chunk], min_memory_mb, processor=scrub_chunk)

        scrubbed_count = sum(1 for r in results if r["scrubbed"])
        print(f"  Processing complete. Scrubbed {scrubbed_count}/{len(results)} files.")
        log_event(f"Processing complete. Scrubbed {scrubbed_count}/{len(results)} files.")
        for r in results:
            if r["warnings"]:
                for w in r["warnings"]:
                    print(f"  {r['filename']}: {w}")

        if sha256:
            from postprocessors.hash_generator import generate_hash
            for file in tqdm(supported, desc="SHA256", unit="file"):
                hashfile = generate_hash(file, algo="sha256")
                print(f"  SHA256 hashfile generated: {hashfile}")
                log_event(f"SHA256 hashfile generated: {hashfile}")
        if gpg_key:
            from postprocessors.gpg_encryptor import encrypt_with_gpg
            for file in tqdm(supported, desc="GPG Encrypt", unit="file"):
                encrypted = encrypt_with_gpg(file, gpg_key)
                print(f"  GPG encrypted: {encrypted}")
                log_event(f"GPG encrypted: {encrypted}")

    def download_results(self, output_dir):
        print(f"Downloading results to {output_dir}...")
        os.makedirs(output_dir, exist_ok=True)
        files = [os.path.join(self.upload_folder, f) for f in os.listdir(self.upload_folder) if os.path.isfile(os.path.join(self.upload_folder, f))]
        if not files:
            print("No processed files to download.")
            return
        for file in files:
            dest = os.path.join(output_dir, os.path.basename(file))
            shutil.copy2(file, dest)
            print(f"  Downloaded: {file} -> {dest}")

    def cleanup(self):
        if os.path.exists(self.upload_folder) and check_uploads_dir(self.upload_folder):
            confirm = input(f"Are you sure you want to securely delete all session files in {self.upload_folder}? (Y/n) ").strip().lower()
            if confirm not in ('y', 'yes', ''):
                print("Cleanup aborted.")
                return
        print("Cleaning up session files...")
        purge_uploads(self.upload_folder)
        print("Cleanup complete.")


def load_renderer(config):
    return CLIRenderer(config)
