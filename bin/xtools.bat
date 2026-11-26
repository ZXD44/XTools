@echo off
setlocal
set "ROOT=%~dp0.."
if exist "%~dp0xtools.exe" (
    "%~dp0xtools.exe" %*
    exit /b %ERRORLEVEL%
)
python "%ROOT%\scripts\hub.py" %*
