@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  set "PYTHON=py"
) else (
  set "PYTHON=python"
)
%PYTHON% -m pip install -r requirements-dev.txt
if errorlevel 1 goto failed
%PYTHON% setup_local.py
if errorlevel 1 goto failed
%PYTHON% -m pytest tests -q
if errorlevel 1 goto failed
%PYTHON% -m unittest discover -s bulk/tests -v
if errorlevel 1 goto failed
echo.
echo Setup and tests passed.
pause
exit /b 0
:failed
echo.
echo Setup or tests failed. See the error above.
pause
exit /b 1
