@echo off
echo ========================================
echo IOPV Web Application Launcher
echo ========================================
echo.

REM 清理可能占用的端口
echo Checking and cleaning ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501') do (
    echo Killing process on port 8501, PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8502') do (
    echo Killing process on port 8502, PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8503') do (
    echo Killing process on port 8503, PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8504') do (
    echo Killing process on port 8504, PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8505') do (
    echo Killing process on port 8505, PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo Ports cleaned. Starting Streamlit...
echo.

cd /d "%~dp0"
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

pause
