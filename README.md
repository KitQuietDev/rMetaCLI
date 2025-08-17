# rMetaCLI v0.1.0 — Clean Your Files, Keep Your Privacy

## Table of Contents

- [rMetaCLI v0.1.0 — Clean Your Files, Keep Your Privacy](#rmetacli-v010--clean-your-files-keep-your-privacy)
  - [Table of Contents](#table-of-contents)
- [Quick Start](#quick-start)
- [Testing your setup](#testing-your-setup)
- [About rMetaCLI](#about-rmetacli)
- [Why rMetaCLI?](#why-rmetacli)
- [Supported Platforms](#supported-platforms)
- [How It Works](#how-it-works)
- [Basic usage and options](#basic-usage-and-options)
- [Supported File Types](#supported-file-types)
- [Privacy Notes](#privacy-notes)
- [Session Management](#session-management)
- [Installation](#installation)
  - [Linux/macOS](#linuxmacos)
  - [Windows](#windows)
- [Example Output](#example-output)
- [Troubleshooting](#troubleshooting)
- [Contact \& Support](#contact--support)
- [Status \& Progress Indicators](#status--progress-indicators)
- [Example Workflow](#example-workflow)
- [License](#license)
- [Contributing](#contributing)
- [Versioning](#versioning)

---

# Quick Start

To get started on Linux or macOS:

```
python3 -m venv ~/.rmeta_venv
source ~/.rmeta_venv/bin/activate
pip install -r /path/to/rmeta_cli/requirements.txt
```

Then run:

```
rmeta file1.pdf file2.docx
rmeta -d /path/to/dir --r --filetype pdf,jpg
rmeta --cleanup
```


For Windows setup, see the [Windows](#windows) section below.

---

# Testing your setup

After installation, you can verify rMetaCLI is working by running:

```
rmeta --dry-run --verbose testfile.pdf
```

This will show detailed output and confirm the CLI is ready to process files. If you see a summary and no errors, your setup is complete.

---

# About rMetaCLI

rMetaCLI is a command-line tool that helps you remove metadata from files without sending anything over the internet. It works entirely offline and supports encryption, hashing, and batch processing. Whether you're a journalist, lawyer, researcher, or just someone who cares about privacy, this tool is built for you.

---

# Why rMetaCLI?

rMetaCLI is designed for privacy-first, batch metadata scrubbing across multiple file types, with ephemeral session management and optional encryption/hashing. Unlike tools like **exiftool** (which focus on image metadata), rMetaCLI provides a unified CLI for PDFs, Office docs, images, and more, with secure deletion and cross-platform support. It never sends your files anywhere and is built for journalists, lawyers, researchers, and anyone who values privacy and simplicity.

---

# Supported Platforms


rMetaCLI works on Linux, Windows, and macOS. As long as you have Python 3.8 or newer and the required libraries installed, you're good to go.

On Linux, install required system libraries using your package manager (e.g., apt, yum, dnf).
On macOS, use Homebrew (e.g., `brew install libjpeg`).
On Windows, the default session folder is `%TEMP%\rmeta_uploads` unless you change it in `config.py` or with environment variables.

---

# How It Works

1. Choose the files or folders you want to clean.
2. rMetaCLI copies them to a temporary session folder.
3. It scrubs metadata and optionally encrypts or hashes the files.
4. Processed files are available in the temporary session folder.
5. Clean up the session manually or let it auto-clean.

---

# Basic usage and options

| Option/Flag                | Description                              | Example Command                                 |
|----------------------------|------------------------------------------|-------------------------------------------------|
| `-d <path>`                | Process files from a folder              | `rmeta -d /path/to/dir`                         |
| `--r`                      | Recursively process subfolders           | `rmeta -d /path/to/dir --r`                     |
| `--filetype pdf,jpg,xlsx`  | Only process specific file types (comma-separated, no spaces)         | `rmeta -d /path/to/dir --filetype pdf,jpg,xlsx` |
| `--gpg-key <path>`         | Encrypt files with your public key       | `rmeta --gpg-key /path/to/key.pub file1.pdf`    |
| `--sha256`                 | Generate SHA256 hash files               | `rmeta --sha256 file1.pdf`                      |
| `--dry-run`                | Preview actions without making changes   | `rmeta --dry-run file1.pdf`                     |
| `--verbose` or `-v`        | Show detailed logs                       | `rmeta --verbose file1.pdf`                     |
| `--cleanup`                | Securely delete session files            | `rmeta --cleanup`                               |
| `--auto-clean-interval`    | Set auto-clean timer (defaults to 600s)        | `rmeta --auto-clean-interval 300`               |
| `--config <path>`          | Use a custom config file (set session folder, auto-clean interval, filetype filters, logging, etc.) | `rmeta --config /path/to/config.py`             |
| `--version`, `--help`      | Show version or help info                | `rmeta --version`                               |

*All flags can be combined as needed. See workflow examples below for advanced usage.*

---

# Supported File Types

- JPEG: Scrubs EXIF metadata
- PDF: Cleans metadata fields
- DOCX: Strips XML tags safely
- XLSX: Removes metadata tags
- HEIC: Converts to JPEG and scrubs
- TXT/CSV: Basic checks only

---

# Privacy Notes
rMetaCLI aims for best-effort cleaning using MIT-compatible libraries. For maximum assurance, verify with external tools.

- **JPEG:** Standard EXIF removed; adversarial/corrupt files may retain data. Use **exiftool** for extra assurance.
- **PDF:** Most metadata fields cleaned; hidden/embedded content may persist. Check with **qpdf** or **exiftool**.
- **DOCX:** XML tags stripped; revision history/embedded objects may remain. Inspect with **Office Document Inspector**.
- **XLSX:** Metadata tags removed; hidden sheets/comments possible. Use **Excel Inspector** for thorough checks.
- **HEIC:** Converted and scrubbed; proprietary tags may linger. Use **exiftool** after conversion.
- **TXT/CSV:** No embedded metadata, but file system attributes (timestamps, permissions) are not scrubbed. Originals are not deleted unless requested.

---

# Session Management

Files are stored temporarily in `/tmp/rmeta_uploads` (or `%TEMP%\rmeta_uploads` on Windows). When cleanup runs, files are overwritten with random data before deletion to reduce recovery risk. Manual cleanup prompts for confirmation. Auto-clean runs in the background based on your settings. The auto-clean interval is configurable in `config.py` or via CLI.

---

# Installation

## Linux/macOS

```
python3 -m venv ~/.rmeta_venv
source ~/.rmeta_venv/bin/activate
pip install -r /path/to/rmeta_cli/requirements.txt
```



Optional shell function:

This allows you to run rmeta from anywhere without typing the full path.

To avoid overwriting an existing alias, you can wrap the function in a conditional:

```
if ! command -v rmeta >/dev/null; then
  rmeta() {
    source ~/.rmeta_venv/bin/activate
    python <project_path>/app.py "$@"
  }
fi
```

To add it automatically:

For bash:

```
echo 'rmeta() { source ~/.rmeta_venv/bin/activate; python <project_path>/app.py "$@"; }' >> ~/.bashrc
source ~/.bashrc
```

For zsh:

```
echo 'rmeta() { source ~/.rmeta_venv/bin/activate; python <project_path>/app.py "$@"; }' >> ~/.zshrc
source ~/.zshrc
```


Or run directly:

```
source ~/.rmeta_venv/bin/activate
python <project_path>/app.py -f /path/to/file.type
```

## Windows

1. Open Command Prompt (cmd) or PowerShell.
2. Create and activate a virtual environment:

  ```cmd
  python -m venv %USERPROFILE%\.rmeta_venv
  %USERPROFILE%\.rmeta_venv\Scripts\activate
  pip install -r C:\path\to\rmeta_cli\requirements.txt
  ```

3. Run rMetaCLI:

  ```cmd
  python C:\path\to\rmeta_cli\app.py -f C:\path\to\file.type
  ```

4. (Optional) Add a batch file or PowerShell alias for convenience:

  PowerShell alias example (add to your PowerShell profile, e.g., $PROFILE):
  ```powershell
  Set-Alias rmeta "python C:\path\to\rmeta_cli\app.py"
  ```

# Example Output


Example: Dry-run mode
```
$ rmeta --dry-run /tmp/rmeta_uploads
[DRY RUN] The following files would be processed:
- dirty.csv
- dirty.docx
- dirty.jpg
- dirty.pdf
- dirty.txt
- dirty.xlsx
Total files: 6
No files were modified.
```

Example: Recursive processing
```
$ rmeta --r --filetype pdf /dir
Copying files to /tmp/rmeta_uploads/...
  Uploaded: /dir/report1.pdf -> /tmp/rmeta_uploads/report1.pdf
  Uploaded: /dir/report2.pdf -> /tmp/rmeta_uploads/report2.pdf
Processing files...
  Auditing 2 files...
  Audit: {'pdf': 2}
  Processing 1 chunks...
  [#####-----] 50% Complete
  Processing complete. Results: {...}
```

Example: GPG encryption and hash
```
$ rmeta --gpg-key /path/to/mykey.pub --sha256 file1.pdf file2.docx
Copying files to /tmp/rmeta_uploads/...
  Uploaded: file1.pdf -> /tmp/rmeta_uploads/file1.pdf
  Uploaded: file2.docx -> /tmp/rmeta_uploads/file2.docx
Processing files...
  Auditing 2 files...
  Audit: {'pdf': 1, 'docx': 1}
  Processing 1 chunks...
  [##########] 100% Complete
  Processing complete. Results: {...}
  SHA256 hashfile generated: /tmp/rmeta_uploads/file1.pdf.sha256
  GPG encrypted: /tmp/rmeta_uploads/file1.pdf.gpg
```

---

# Troubleshooting

- If you see missing library errors, install system packages like `libjpeg-dev` or `libssl-dev`.
- If you get permission errors, try running with `sudo` or adjust folder permissions.
- If you see Python version errors, check with `python3 --version`.
- Check if your virtual environment is activated (`which python` should point to your venv).
- Run `pip list` to confirm dependencies are installed.
- Use `--verbose` for more detailed logs.
- For best results, stick with the virtual environment and shell function setup.
- Packaging as a single executable is not recommended due to Python shared library issues on Linux.

---

# Contact & Support

Have questions, run into issues, or want to request a feature? Open an issue on GitHub or reach out to KitQuietDev.

---

# Status & Progress Indicators

rMetaCLI prints progress messages during file upload, processing, and cleanup. Use `--verbose` to see detailed logs. For large batches, you’ll get per-file updates and a summary at the end.

---

# Example Workflow

1. Process files:

```
rmeta file1.pdf file2.docx
rmeta --r --filetype pdf /dir
rmeta --gpg-key /path/to/key.pub --sha256 file1.pdf file2.docx
rmeta --dry-run --verbose file1.pdf file2.docx
```

2. Clean up:

```
rmeta --cleanup
```

---

# License

rMetaCLI is licensed under MIT. See `LICENSE` for details. Third-party licenses are listed in `THIRD_PARTY.md`.

---

# Contributing

Want to add support for a new file type or suggest a feature? The code is modular and easy to extend. Contributions are welcome! If you’re submitting a pull request, please follow the coding style and include tests where possible. See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for coding style and test requirements.

---

# Versioning

Check `CHANGELOG.md` for version history and detailed updates.
