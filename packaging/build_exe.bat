@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0\.."

if not exist ".venv\Scripts\pyinstaller.exe" (
    echo Creating virtual environment and installing dependencies...
    python -m venv .venv
    ".venv\Scripts\pip.exe" install -r requirements.txt
)

".venv\Scripts\python.exe" packaging\make_icon.py

".venv\Scripts\pyinstaller.exe" ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onedir ^
  --name "PDF整理工具" ^
  --icon "assets\applogo.ico" ^
  --add-data "assets\applogo.png;assets" ^
  --add-data "assets\applogo.ico;assets" ^
  --collect-data certifi ^
  --hidden-import truststore ^
  --exclude-module tkinter ^
  --exclude-module onnxruntime ^
  --exclude-module numpy ^
  --exclude-module networkx ^
  --exclude-module pymupdf4llm ^
  --exclude-module pymupdf_layout ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtWebEngineQuick ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.Qt3DRender ^
  --exclude-module PySide6.QtMultimedia ^
  --exclude-module PySide6.QtMultimediaWidgets ^
  --exclude-module PySide6.QtCharts ^
  --exclude-module PySide6.QtGraphs ^
  --exclude-module PySide6.QtSql ^
  --exclude-module PySide6.QtTest ^
  app.py

set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
    "%ISCC%" packaging\installer.iss
    echo.
    echo Installer selesai: installer_output\PDF整理工具_Setup.exe
) else (
    echo Inno Setup 6 tidak ditemukan. Folder aplikasi tersedia di: dist\PDF整理工具
)
endlocal
