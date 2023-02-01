@echo off
cd /d "%~dp0"
setlocal
python fetch.py dump %*
