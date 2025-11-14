@echo off
REM Create venv if it doesn't exist
IF NOT EXIST "venv" (
    echo Creating virtual environment...
    python -m venv venv
) ELSE (
    echo Virtual environment already exists.
)

REM Activate the venv in this script and install requirements
call venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing requirements...
pip install -r "%~dp0requirements.txt"

echo.
echo Done. To use the environment, run:
echo    venv\Scripts\activate
exit /B 0
