# Developer notes

Notes for anyone extending or maintaining rMetaCLI.

## Project layout

```
.
├── app.py                    # Entry point
├── config.py                 # Env/.env configuration loading
├── renderer/cli_renderer.py  # Argument parsing and command dispatch
├── handlers/                 # File-type-specific metadata scrubbers
├── postprocessors/           # Optional extras: GPG, hashing
├── utils/                    # Cleanup, chunking, memory checks, PII scanning
├── rmeta.1                   # Man page
└── docs/                     # This file and related docs
```

This is the CLI counterpart to [rMeta](https://github.com/KitQuietDev/rMeta), which wraps the same handlers in a Flask web UI. If you're adding a file handler or postprocessor, the two projects share the same pattern — check rMeta's `docs/DEVELOPERS.md` too if you're maintaining both.

## Adding a file handler

1. Create a new `.py` file in `handlers/`, named `<type>_handler.py`.
2. Define `SUPPORTED_EXTENSIONS = {"ext1", "ext2"}` (lowercase) and a `scrub(file_path)` function.
3. `handlers/__init__.py` auto-discovers any `*_handler.py` module and registers it by extension at startup — nothing else to wire up.

## Adding a postprocessor

1. Create a `.py` file in `postprocessors/`.
2. Implement a callable, e.g. `generate_hash(...)`.
3. Wire the call into `renderer/cli_renderer.py`'s `process_files()`, gated behind a CLI flag if it should be optional.

## How processing actually flows

`CLIRenderer.process_files()` audits and chunks the uploaded files, then calls `process_chunks()` with a `scrub_chunk` callback. That callback is what looks up each file's handler via `get_handler_for_extension()` and calls `scrub()` — if you're debugging why a file type isn't being cleaned, start there rather than in `utils/chunking.py`.

## Testing

There's no formal test suite yet. To sanity-check changes:

```bash
python app.py --dry-run --verbose file1.pdf
```

Or run against the sample dirty files in rMeta's `dev/generated_dirty_files_for_test/` if you have that repo checked out alongside this one.

## Packaging

`rmeta.1` documents the CLI's flags — if you add or rename an argument in `cli_renderer.py`, update the man page in the same change. Packaging as a single PyInstaller executable is not recommended on Linux due to shared-library issues; see the Troubleshooting section in the README.

## License

MIT.
