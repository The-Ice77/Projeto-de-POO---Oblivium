@echo off
setlocal
cd /d "%~dp0"
rem As comparacoes de errorlevel aceitam somente zero, inclusive para erros negativos.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
    if not errorlevel 1 if errorlevel 0 (
        ".venv\Scripts\python.exe" iniciar.py %*
        goto resultado
    )
)
where py >nul 2>&1
if errorlevel 1 goto python_padrao
for %%V in (3.13 3.12 3.11 3.10) do (
    py -%%V -c "import sys" >nul 2>&1
    if not errorlevel 1 if errorlevel 0 (
        py -%%V iniciar.py %*
        goto resultado
    )
)
:python_padrao
python iniciar.py %*
:resultado
set "oblivium_resultado=%errorlevel%"
if not "%oblivium_resultado%"=="0" pause
exit /b %oblivium_resultado%
