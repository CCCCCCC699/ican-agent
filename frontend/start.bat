@echo off
chcp 65001 >nul
title 申城智行 - 前端演示
cd /d %~dp0
echo.
echo  ==========================================
echo   申城智行  前端演示模式
echo   浏览器将自动打开 http://localhost:8080
echo   关闭本窗口即停止服务
echo  ==========================================
echo.
timeout /t 1 >nul
start "" http://localhost:8080
"D:\conda_envs\cnm\python.exe" mock_server.py
pause
