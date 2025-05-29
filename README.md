# Radio Inventory Management System

## Overview

A full-featured desktop application for managing radio inventory for departments within an organization. Designed with a clean, professional UI and support for tracking radio assignments, service records, and status changes. Built with `tkinter` and `sqlite3`, and supports exportable reports, user shortcuts, and tooltips for improved user experience.

---

## Features

**Radio Management**

- Add, edit, or delete radios
- Assign radios to departments or individuals
- Track received, issued, returned dates
- Toggle missing/found and in-service/out-of-service states

**Service Tracking**

- Log service records with LRC#, technician, repair details, and notes
- View all service history for a specific radio
- View full service record history for all radios

**Reports**

- Generate professional Excel reports with logo, title, subtitle, and styled headers
- Save reports locally for recordkeeping or audits

**Enhanced UI**

- Radios in **yellow** for in-service
- Radios in **red** for missing
- Tooltips for buttons and fields
- Keyboard shortcuts:

  - `Ctrl + N` → Add radio
  - `Ctrl + D` → Delete selected
  - `Ctrl + E` → Edit selected
  - `Ctrl + M` → Toggle missing/found
  - `Ctrl + S` → Open services window

---

## Setup

### Requirements

- Python 3.10+
- `venv` (recommended)

### Installation

```bash
# Clone the repo
https://github.com/jtarkington-dev/radio-inventory.git
cd radio-inventory

# Create and activate virtual environment
python -m venv venv
./venv/Scripts/activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

### Packaging as EXE

This project supports building a standalone `.exe` using `pyinstaller`:

```bash
pyinstaller --onefile --windowed --icon=radio.ico main.py
```

Resulting `.exe` will appear in the `dist/` folder.

---

## Database

The `radios.db` file is generated in the same directory as `main.py`. It uses SQLite and supports WAL mode to reduce lock contention.

---

## Testing

Automated tests can be run using:

```bash
python -m tests.test_database
```

Test results are output to the `/test_report/` directory in HTML format.

---

## Author

**Jeremy Tarkington**
[GitHub](https://github.com/jtarkington-dev)

---

## License

MIT License
