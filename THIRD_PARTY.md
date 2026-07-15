# Third-party libraries

Libraries rMetaCLI actually depends on at runtime, and the license each is distributed under. License info here is a courtesy summary, not legal advice — check each project's own license file if you need certainty.

| Library | Purpose | Used in | License |
|---|---|---|---|
| pypdf | PDF metadata handling | `handlers/pdf_handler.py` | BSD-3-Clause |
| pdfplumber / pdfminer.six | PDF text extraction (for PII scanning) | `handlers/pdf_handler.py` | MIT |
| python-docx | Word document parsing | `handlers/docx_handler.py` | MIT |
| openpyxl | Excel file parsing | `handlers/xlsx_handler.py` | MIT |
| pillow | Image handling | `handlers/heic_handler.py`, `handlers/image_handler.py` | MIT-CMU |
| pillow_heif | HEIC/HEIF decoding | `handlers/heic_handler.py` | BSD-3-Clause |
| piexif | EXIF read/write | image handlers | MIT |
| pyheif | HEIC decoding | `handlers/heic_handler.py` | LGPL-3.0 |
| nometa | Metadata stripping helper | handlers | MIT |
| lxml | XML processing | DOCX/XLSX handlers | BSD-3-Clause |
| cryptography | Crypto primitives | supporting hashing/encryption | Apache-2.0 / BSD-3-Clause (dual) |
| python-dotenv | `.env` loading | `config.py` | BSD-3-Clause |
| tqdm | Progress bars | `renderer/cli_renderer.py` | MIT |
| psutil | Memory/resource checks | `utils/system.py` | BSD-3-Clause |
| aiofiles | Async file I/O | handlers (async paths) | Apache-2.0 |
| PyYAML | YAML parsing | config/tooling | MIT |
| typing_extensions | Typing backports | type hints | PSF-2.0 |

GPG encryption (`postprocessors/gpg_encryptor.py`) shells out to the system's own `gpg` binary rather than bundling a GPG library — that binary's license is whatever your OS/distribution provides.

## Development tooling

Not shipped in the running app — used for linting, formatting, and pre-commit hooks during development: `black`, `pre-commit`, `pyflakes`, `pycodestyle`, `mccabe`, `mypy_extensions`, `virtualenv`, `filelock`, `platformdirs`, `identify`, `cfgv`, `nodeenv`, `distlib`.

Thanks to the maintainers of all of the above.
