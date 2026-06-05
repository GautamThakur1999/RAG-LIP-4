@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python eval\run_daily_job.py >> eval\daily_job_output.log 2>&1
