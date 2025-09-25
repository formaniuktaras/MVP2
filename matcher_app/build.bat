@echo off
SETLOCAL
IF NOT EXIST .venv (
    echo Створіть середовище .venv перед збіркою.
    exit /b 1
)
CALL .venv\Scripts\activate.bat
pyinstaller --noconfirm --clean --onefile --windowed --name "MatcherApp" --icon icon.ico main.py
ENDLOCAL
