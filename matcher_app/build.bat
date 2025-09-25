@echo off
SETLOCAL
IF NOT EXIST .venv (
    echo Створіть середовище .venv перед збіркою.
    exit /b 1
)
CALL .venv\Scripts\activate.bat
SET "ICON_ARG="
python -c "import pathlib, sys; p = pathlib.Path('icon.ico'); data = p.read_bytes() if p.exists() else b''; status = 0 if p.exists() and len(data) >= 22 and data[:4] == b'\0\0\x01\0' else (1 if not p.exists() else 2); sys.exit(status)"
IF %ERRORLEVEL% EQU 0 (
    SET "ICON_ARG=--icon icon.ico"
) ELSE IF %ERRORLEVEL% EQU 1 (
    echo Попередження: icon.ico не знайдено. PyInstaller використає стандартну іконку.
) ELSE (
    echo Попередження: icon.ico має некоректний формат. PyInstaller використає стандартну іконку.
    echo Замініть icon.ico на валідний ICO-файл, щоб мати власну іконку.
)
pyinstaller --noconfirm --clean --onefile --windowed --name "MatcherApp" %ICON_ARG% main.py
ENDLOCAL
