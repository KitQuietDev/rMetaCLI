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

        subparsers = parser.add_subparsers(dest="command")
        download_parser = subparsers.add_parser("download", help="Download processed results")
        download_parser.add_argument("output", help="Output directory")
        cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup session files")

        args = parser.parse_args()
        self.start_auto_cleanup(interval_override=args.auto_clean_interval)

        if args.verbose:
            print("[VERBOSE] Arguments:", args)

        # File or directory processing
        if args.files:
            uploaded = self.upload_files(args.files, recursive=False, filetype=args.filetype, verbose=args.verbose)
            self.process_files(files=uploaded, filetype=args.filetype, verbose=args.verbose)
            return
        elif args.dir:
            uploaded = self.upload_files([args.dir], recursive=args.r, filetype=args.filetype, verbose=args.verbose)
            self.process_files(files=uploaded, filetype=args.filetype, verbose=args.verbose)
            return

        # Subcommands
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
                    # Process only top-level files in the directory
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
        # Only process files just uploaded, unless files is None (fallback to all in session dir)
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
        chunks = chunk_files_by_size(supported, chunk_mb)
        print(f"  Processing {len(chunks)} chunks...")
        results = []
        for chunk in tqdm(chunks, desc="Processing", unit="chunk"):
            result = process_chunks([chunk], min_memory_mb)
            results.append(result)
            for file in chunk:
                log_event(f"Processed {file}")
        print(f"  Processing complete. Results: {results}")
        log_event(f"Processing complete. Results: {results}")
        if sha256:
            from postprocessors.import_hashlib import generate_hash
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
import os
import threading
import time
import argparse
import shutil
from tqdm import tqdm
from datetime import datetime
from config import load_config
from utils.cleanup import purge_uploads, check_uploads_dir
from utils.chunking import audit_files, chunk_files_by_size, process_chunks

                        # --- Clean, robust CLI implementation ---


# Loader for app.py

def load_renderer(config):
    return CLIRenderer(config)
    return CLIRenderer(config)
    return CLIRenderer(config)
