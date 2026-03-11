@echo off
REM 收盘保存任务 (15:00)
REM Windows任务计划程序调用此脚本

cd /d "%~dp0"
python nav_scheduler.py close
