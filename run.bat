@echo off
set VENV_NAME=mtvenv
set REQUIREMENTS=requirements.txt
set PYTHON_EXEC=python
set SCRIPT_NAME=moslem_tools.py
if not exist %VENV_NAME% (
    echo Virtual environment not found. Creating...
    %PYTHON_EXEC% -m venv %VENV_NAME%
    echo Installing requirements...
    call %VENV_NAME%\Scripts\activate && pip install -r %REQUIREMENTS%
)
echo running moslem tools ...
call %VENV_NAME%\Scripts\activate
cd moslemTools
%PYTHON_EXEC% %SCRIPT_NAME%