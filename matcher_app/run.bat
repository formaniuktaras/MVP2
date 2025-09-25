@echo off
SETLOCAL
IF NOT EXIST .venv (
    echo Створіть середовище .venv перед запуском.
    exit /b 1
)
CALL .venv\Scripts\activate.bat
python main.py
ENDLOCAL
