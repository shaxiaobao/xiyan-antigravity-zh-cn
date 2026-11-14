@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "ACTION=launch"
if /I "%~1"=="status" set "ACTION=status"
if /I "%~1"=="restore" set "ACTION=restore"
if /I "%~1"=="apply" set "ACTION=apply"
py -3 -c "import sys; assert sys.version_info >= (3, 9)" >nul 2>&1
if not errorlevel 1 goto use_py
python -c "import sys; assert sys.version_info >= (3, 9)" >nul 2>&1
if not errorlevel 1 goto use_python
echo Python 3.9+ is required. Install it from https://www.python.org/downloads/windows/
pause
exit /b 1
:use_py
py -3 "%~dp0patch_asar.py" %ACTION%
goto done
:use_python
python "%~dp0patch_asar.py" %ACTION%
:done
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo See the error above. Custom install: set ANTIGRAVITY_PATH to your installation folder.
if not "%RESULT%"=="0" pause
if /I not "%ACTION%"=="launch" if "%RESULT%"=="0" pause
exit /b %RESULT%
