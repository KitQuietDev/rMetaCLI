# config.py

import os
import logging
import secrets
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# rMetaCLI Configuration Loader
#
# Purpose: Loads all runtime configuration from environment and .env files.
# Audience: Anyone running rMetaCLI who wants to tweak privacy, session, or resource settings.
#
# This module is intentionally explicit—no magic, no surprises.

def load_config():
    """
    Loads configuration from environment variables and .env file.
    
    Returns:
        dict: Configuration dictionary with all required settings.
    """
    # Load .env file if it exists
    load_dotenv()
    
    config = {
        "SESSION_TIMEOUT": int(os.getenv("SESSION_TIMEOUT", 600)),
        "FLASK_RUN_PORT": int(os.getenv("FLASK_RUN_PORT", 8574)),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "SESSIONS_ROOT": os.getenv("SESSIONS_ROOT", "uploads"),
        "ALLOW_HASH": os.getenv("ALLOW_HASH", "true").lower() == "true",
        "ALLOW_GPG": os.getenv("ALLOW_GPG", "true").lower() == "true",
        "MAX_HANDLER_TIMEOUT": int(os.getenv("MAX_HANDLER_TIMEOUT", 30)),
        "MIN_MEM_MB": int(os.getenv("MIN_MEM_MB", 512)),
        "SECRET_KEY": os.getenv("SECRET_KEY") or secrets.token_hex(32),  # Secure default
        # Use /tmp/rmeta_uploads for CLI ephemeral sessions by default
        "UPLOAD_FOLDER": os.getenv("UPLOAD_FOLDER", "/tmp/rmeta_uploads"),
        "AUTO_CLEAN_INTERVAL": int(os.getenv("AUTO_CLEAN_INTERVAL", 600)),  # seconds
    }
    
    # Create upload directory if it doesn't exist
    upload_dir = config["UPLOAD_FOLDER"]
    if not os.path.exists(upload_dir):
        try:
            os.makedirs(upload_dir, exist_ok=True)
            logger.info(f"📁 Created upload directory: {upload_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to create upload directory {upload_dir}: {e}")
            raise RuntimeError(f"Cannot create upload directory: {e}")
    
    logger.info(f"⚙️ Configuration loaded: {len(config)} settings")
    return config

    # Ensure upload directory exists (privacy: don't leak files elsewhere)