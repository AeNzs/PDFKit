# PDF整理工具

Desktop utility built with **PySide6** combining 5 daily PDF & Excel file workflows into one multilingual Windows interface (**Bahasa Indonesia**, **简体中文**, **English**) with Light/Dark theme support.

## Features

1. **01 PDF Split & Auto-Sign**
   - Splits a multi-page PDF based on Excel keywords (Column A: keyword, Column B: output filename).
   - Inserts PNG/JPG signatures automatically using text-anchor search (`PyMuPDF`) or fixed page coordinates.
   - Configurable rules editor with JSON save/load (`%APPDATA%\PDF整理工具\signature_rules.json`).
2. **02 Excel Batch File Mover**
   - Reads `mapping.xlsx` directly via `openpyxl` (no Microsoft Excel required).
   - Auto-detects `mapping.xlsx` in current/parent directories, previews rows before moving, and reports real Moved / Not Found / Error counts.
3. **03 Folder & File List Exporter**
   - Generates UTF-8 text lists (`folderlist.txt`, `filelist.txt`, `folder_file_list.txt`) with live preview before exporting.

## Project Structure

```text
PDF整理工具/
├── app.py                  # Application entry point
├── requirements.txt        # Python dependencies
├── assets/                 # App logo PNG & Windows multi-size ICO
│   ├── applogo.png
│   └── applogo.ico
├── core/                   # Business logic & i18n
│   ├── i18n.py
│   ├── pdf_sign.py
│   ├── file_mover.py
│   └── list_exporter.py
├── ui/                     # PySide6 GUI & Light/Dark themes
│   ├── main_window.py
│   ├── theme.py
│   ├── widgets.py
│   ├── tab_pdf_sign.py
│   ├── tab_file_mover.py
│   └── tab_list_exporter.py
└── packaging/              # Build & Windows installer scripts
    ├── make_icon.py
    ├── build_exe.bat
    └── installer.iss
```

## Run From Source

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Build Windows Installer (`PDF整理工具_Setup.exe`)

Requires **Python 3.11+** and **Inno Setup 6**:

```powershell
.\packaging\build_exe.bat
```

Output installer is written to `installer_output\PDF整理工具_Setup.exe`.
