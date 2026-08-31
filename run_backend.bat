@echo off
title NER Landslide AI - Backend (FastAPI : 8000)
cd /d "%~dp0backend"
echo ============================================
echo  NER Landslide AI - Backend
echo  API:      http://127.0.0.1:8000
echo  Swagger:  http://127.0.0.1:8000/docs
echo ============================================
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
