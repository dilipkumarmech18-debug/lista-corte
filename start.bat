@echo off
title Lista de Corte por Materiais
color 1F

:: Activate virtual environment
call "%~dp0venv\Scripts\activate.bat"

:: Open browser after 3 seconds
start /b cmd /c "timeout /t 3 >nul && start http://localhost:8501"

:: Run app
echo  A iniciar Lista de Corte...
echo  Abre o browser em: http://localhost:8501
echo  Para fechar: pressiona Ctrl+C
echo.
streamlit run "%~dp0app.py" --server.headless true --browser.gatherUsageStats false
