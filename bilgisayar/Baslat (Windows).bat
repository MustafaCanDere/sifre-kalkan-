@echo off
chcp 65001 >nul
python "%~dp0sifre_kontrol.py" || py "%~dp0sifre_kontrol.py"
pause
