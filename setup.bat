@echo off
title Lista de Corte - Setup
color 1F
echo.
echo  ============================================
echo   Lista de Corte por Materiais - Setup
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python nao encontrado!
    echo.
    echo  Por favor instala Python em: https://www.python.org/downloads/
    echo  Certifica-te de marcar "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo  [OK] Python encontrado.

:: Create virtual environment
echo.
echo  A criar ambiente virtual...
python -m venv venv
if %errorlevel% neq 0 (
    echo  [ERROR] Falha ao criar ambiente virtual.
    pause
    exit /b 1
)
echo  [OK] Ambiente virtual criado.

:: Install requirements
echo.
echo  A instalar dependencias (pode demorar alguns minutos)...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo  [OK] Dependencias instaladas.

:: Create start shortcut on Desktop
echo.
echo  A criar atalho no Ambiente de Trabalho...
set SCRIPT_DIR=%~dp0
set SHORTCUT=%USERPROFILE%\Desktop\Lista de Corte.lnk
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%SCRIPT_DIR%start.bat'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.IconLocation = 'shell32.dll,162'; $s.Description = 'Lista de Corte por Materiais'; $s.Save()"
echo  [OK] Atalho criado no Ambiente de Trabalho.

echo.
echo  ============================================
echo   Instalacao concluida com sucesso!
echo  ============================================
echo.
echo  Clica duas vezes em "Lista de Corte" no
echo  Ambiente de Trabalho para iniciar a app.
echo.
pause
