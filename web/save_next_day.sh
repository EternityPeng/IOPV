#!/bin/bash
# 次日保存任务 (05:00)
# Linux cron 调用此脚本

cd "$(dirname "$0")"
python nav_scheduler.py next_day
