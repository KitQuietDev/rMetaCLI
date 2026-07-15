# Changelog

All notable changes to this project will be documented here.  
This format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.0] - 2026-07-15

### Fixed
- The processing pipeline was completely disconnected from the actual scrubbing logic: `cli_renderer.py` called `process_chunks()` with no processor callback, so files were uploaded and "processed" but never actually had metadata stripped. Now wires up real handler dispatch, mirroring rMeta's upload flow.
- `--gpg-key`, `--sha256`, `--dry-run`, and `--clean-after` were documented in the README and man page but never actually exposed as CLI flags — only as unreachable internal method parameters. Now wired into argparse for real.
- `cli_renderer.py` had imports declared after the class body, a stray floating comment, and a `load_renderer()` with three duplicate dead `return` statements.
- `--version` incorrectly reported `rMeta CLI v0.4.0` (copy-pasted from the sibling repo) instead of this project's own version.

### Changed
- Handlers, postprocessors, and cleanup/chunking/PII-scanning utilities extracted into [rmeta-core](https://github.com/KitQuietDev/rmeta-core), shared with rMeta.
- Added a real CI workflow (previously none existed).
- Dependabot-relevant dependencies (python-dotenv, black, filelock, virtualenv) bumped to patched versions.

## [0.1.0] - 2025-08-17

### Initial Public Release
- Basic metadata scrubbing.
- HEIC handler and rudimentary postprocessing.
