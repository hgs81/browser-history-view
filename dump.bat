@echo off
cd /d "%~dp0"
setlocal
if not exist backup mkdir backup
set TIMESTRING=%DATE:/=_%

python fetch.py dump | bin\zip.exe -r backup\results-%USERNAME%-%TIMESTRING: =_%.zip . -x "*.zip" -x "backup/*" -x "bin/*" -x "*.exe" -x "hbd" -x "*.txt" -x "*.bat" -x "*.sh" -x "*.php" -x "*.py" -x "*.pyc" -x "*__pycache__/*" -x "*.gitignore" -x ".git/*" -x "*.DS_Store*" -z
