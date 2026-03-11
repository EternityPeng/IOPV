@echo off
REM 次日保存任务 (05:00)
REM Windows任务计划程序调用此脚本

cd /d "%~dp0"
python nav_scheduler.py next_day
