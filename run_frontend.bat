@echo off
title NER Landslide AI - Frontend (Vite : 5173)
cd /d "%~dp0frontend"
if not exist node_modules (
    echo Installing frontend dependencies ^(first run^)...
    call npm install
)
echo ============================================
echo  NER Landslide AI - Frontend
echo  App: http://localhost:5173
echo ============================================
call npm run dev
pause
