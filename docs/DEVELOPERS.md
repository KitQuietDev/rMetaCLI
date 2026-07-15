# Developer notes

Notes for anyone extending or maintaining rMetaCLI.

## Project layout

```
.
├── app.py                    # Entry point
├── config.py                 # Env/.env configuration loading
├── renderer/cli_renderer.py  # Argument parsing and command dispatch
├── rmeta.1                   # Man page
└── docs/                     # This file and related docs
```

Handlers, postprocessors, and shared utilities (cleanup, chunking, PII scanning) live in the separate [rmeta-core](https://github.com/KitQuietDev/rmeta-core) package, not in this repo — it's pulled in via `requirements.txt` and shared with [rMeta](https://github.com/KitQuietDev/rMeta) (the Flask web frontend for the same handlers).

## Adding a file handler

Handlers live in `rmeta-core`, not here. In that repo:

1. Create a new `.py` file in `rmeta_core/handlers/`, named `<type>_handler.py`.
2. Define `SUPPORTED_EXTENSIONS = {"ext1", "ext2"}` (lowercase) and a `scrub(file_path)` function.
3. `rmeta_core/handlers/__init__.py` auto-discovers any `*_handler.py` module and registers it by extension at startup.
4. Tag a new `rmeta-core` release and bump the pin in this repo's `requirements.txt` to pick it up.

## Adding a postprocessor

Also in `rmeta-core`:

1. Create a `.py` file in `rmeta_core/postprocessors/`.
2. Implement a callable, e.g. `generate_hash(...)`.
3. Tag a release, bump the pin here, then wire the call into `renderer/cli_renderer.py`'s `process_files()`, gated behind a CLI flag if it should be optional.

## How processing actually flows

`CLIRenderer.process_files()` audits and chunks the uploaded files, then calls `process_chunks()` with a `scrub_chunk` callback. That callback is what looks up each file's handler via `get_handler_for_extension()` and calls `scrub()` — if you're debugging why a file type isn't being cleaned, start there rather than in `rmeta-core`'s `utils/chunking.py`.

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
