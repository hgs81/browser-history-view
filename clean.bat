@echo off
cd /d "%~dp0"

for /D %%I in ("Chrome *") do (del /f /s /q "%%~I" >NUL && rmdir "%%~I")
for /D %%I in ("Profile *") do (del /f /s /q "%%~I" >NUL && rmdir "%%~I")
for /D %%I in ("*-*-*-*") do (del /f /s /q "%%~I" >NUL && rmdir "%%~I")
for /D %%I in ("results\*") do (del /f /s /q "%%~I" >NUL && rmdir "%%~I")
for %%I in (__pycache__ results extension localStorage chromiumKey bookmark cookie creditCard download history password) do (
    if exist "%%~I" del /f /s /q "%%~I" >NUL && rmdir "%%~I" >NUL 2>NUL
)
