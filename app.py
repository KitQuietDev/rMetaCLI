# app.py

import sys
from config import load_config
from renderer.cli_renderer import load_renderer as load_cli_renderer
from utils.cleanup import purge_uploads, start_auto_cleanup, stop_all_cleanup
from utils.chunking import audit_files, chunk_files_by_size, process_chunks
from utils.system import get_available_memory_mb

# Entry point: wires together config, cleanup, and the CLI renderer.
# No web server, no Docker required — everything runs locally.

def handle_shutdown():
    """Gracefully handle shutdown signals (Ctrl+C, etc.), stopping cleanup
    threads and securely deleting session files."""
    print("Received shutdown signal. Cleaning up...")
    stop_all_cleanup()
    purge_uploads("/tmp/rmeta_uploads")
    sys.exit(0)

def create_cli():
    """Load configuration, start auto-cleanup, and return the CLI renderer."""
    config = load_config()
    if config is None:
        raise RuntimeError("Configuration could not be loaded!")
    upload_folder = config.get("UPLOAD_FOLDER", "/tmp/rmeta_uploads")
    session_timeout = config.get("SESSION_TIMEOUT", 600)
    start_auto_cleanup(upload_folder, session_timeout)
    renderer = load_cli_renderer(config)
    return renderer

def main():
    renderer = create_cli()
    try:
        renderer.run()
    except KeyboardInterrupt:
        print("Received KeyboardInterrupt")
        handle_shutdown()

if __name__ == "__main__":
    main()
