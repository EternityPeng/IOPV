#!/bin/bash
# 收盘保存任务 (15:00)
# Linux cron 调用此脚本

cd "$(dirname "$0")"
python nav_scheduler.py close
