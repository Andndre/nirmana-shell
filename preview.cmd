@echo off
setlocal

set "INPUT=%~1"
if "%INPUT%"=="" goto :eof

for /f "tokens=1,2" %%A in ("%INPUT%") do (
    if "%%B"=="" (
        set "THEME=%%A"
    ) else (
        set "THEME=%%B"
    )
)

set "TARGET=%~dp0.previews\%THEME%.txt"

if exist "%TARGET%" (
    type "%TARGET%"
) else (
    echo.
    echo   Theme: %THEME%
    echo   [No preview cache found at %TARGET%]
)
