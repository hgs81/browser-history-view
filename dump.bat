@echo off
cd /d "%~dp0"
setlocal
if not exist backup mkdir backup
set TIMESTRING=%DATE:/=_%

if "%DRY_RUN%" equ "" python fetch.py dump > profiles.info
bin\7z.exe a -tzip backup\results-%USERNAME%-%TIMESTRING: =_%.zip . -x!*.py* x!*.zip -x!*.exe -x!hbd -x!*.txt -x!*.bat -x!*.sh -xr!.* -xr!backup -xr!bin -xr!__pycache__
endlocal
