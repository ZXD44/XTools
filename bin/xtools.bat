@echo off
chcp 65001 >nul
setlocal
set "ROOT=%~dp0.."
python "%ROOT%\scripts\hub.py" %*
endlocal
