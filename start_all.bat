@echo off
title NER Landslide AI
echo Starting NER Landslide AI (backend + frontend)...
start "NER-AI Backend"  cmd /k "%~dp0run_backend.bat"
timeout /t 5 /nobreak >nul
start "NER-AI Frontend" cmd /k "%~dp0run_frontend.bat"
echo.
echo Both windows launched:
echo   Backend  : http://127.0.0.1:8000/docs
echo   Frontend : http://localhost:5173
echo Close the windows to stop the services.
