@echo off
setlocal
cd /d "%~dp0"
python %~dp0fetch.py %*
