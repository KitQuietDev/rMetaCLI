# app.py

import sys
from config import load_config
from renderer.cli_renderer import load_renderer as load_cli_renderer
from utils.cleanup import purge_uploads, start_auto_cleanup, stop_all_cleanup
from utils.chunking import audit_files, chunk_files_by_size, process_chunks
from utils.system import get_available_memory_mb

# rMetaCLI Application Entry Point
#
# Purpose: Launches the CLI, manages session lifecycle, and ensures privacy-first operation.
# Audience: Anyone who wants to clean files locally—no web server, no Docker required.
#
# This file is intentionally simple. It wires together config, cleanup, and the CLI renderer.

def handle_shutdown():
    print("🛑 Received shutdown signal. Cleaning up...")
    stop_all_cleanup()
    purge_uploads("/tmp/rmeta_uploads")
    sys.exit(0)

    """
    Gracefully handle shutdown signals (Ctrl+C, etc).
    Ensures all cleanup threads are stopped and session files are securely deleted.
    """

def create_cli():
    config = load_config()
    if config is None:
        raise RuntimeError("Configuration could not be loaded!")
    upload_folder = config.get("UPLOAD_FOLDER", "/tmp/rmeta_uploads")
    session_timeout = config.get("SESSION_TIMEOUT", 600)
    # Start the auto cleanup timer
    start_auto_cleanup(upload_folder, session_timeout)
    renderer = load_cli_renderer(config)
    return renderer

    """
    Loads configuration, starts auto-cleanup, and returns the CLI renderer.
    """

def main():
    renderer = create_cli()
    try:
        renderer.run()
    except KeyboardInterrupt:
        print("🛑 Received KeyboardInterrupt")
        handle_shutdown()

    """
    Main entry point for rMetaCLI.
    Launches the CLI renderer and handles graceful shutdown.
    """

if __name__ == "__main__":
    main()