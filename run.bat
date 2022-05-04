@echo off
setlocal
cd /d "%temp%"
python %~dp0fetch.py %*
endlocal
