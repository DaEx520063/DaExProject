@echo off
chcp 65001 >nul
title ตั้งค่าฐานข้อมูล DaEx System

echo.
echo ========================================
echo    ตั้งค่าฐานข้อมูล DaEx System
echo ========================================
echo.

:menu
echo เลือกการดำเนินการ:
echo.
echo 1. สร้างฐานข้อมูลใหม่จากไฟล์ SQL
echo 2. แยกไฟล์ SQL เป็นส่วนๆ
echo 3. รวมไฟล์ SQL ส่วนๆ กลับเป็นไฟล์เดียว
echo 4. ติดตั้งและตั้งค่า Git LFS
echo 5. ออกจากโปรแกรม
echo.
set /p choice="กรุณาเลือก (1-5): "

if "%choice%"=="1" goto create_db
if "%choice%"=="2" goto split_sql
if "%choice%"=="3" goto merge_sql
if "%choice%"=="4" goto setup_lfs
if "%choice%"=="5" goto exit
echo.
echo ❌ กรุณาเลือก 1, 2, 3, 4, หรือ 5
echo.
goto menu

:create_db
echo.
echo 🔧 สร้างฐานข้อมูลใหม่จากไฟล์ SQL
echo.
python create_database_from_sql.py
echo.
pause
goto menu

:split_sql
echo.
echo ✂️ แยกไฟล์ SQL เป็นส่วนๆ
echo.
python split_sql_file.py
echo.
pause
goto menu

:merge_sql
echo.
echo 🔗 รวมไฟล์ SQL ส่วนๆ กลับเป็นไฟล์เดียว
echo.
python split_sql_file.py
echo.
pause
goto menu

:setup_lfs
echo.
echo 🚀 ติดตั้งและตั้งค่า Git LFS
echo.
python setup_git_lfs.py
echo.
pause
goto menu

:exit
echo.
echo 👋 ขอบคุณที่ใช้งาน
echo.
pause
exit
