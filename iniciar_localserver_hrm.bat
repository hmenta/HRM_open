@echo off
title HRM Open - Servidor Local
color 0A
echo ==========================================
echo    INICIANDO HRM OPEN - MODO LOCAL
echo ==========================================
cd /d C:\Users\hment\Desktop\hrm_open

echo [1/2] Activando entorno virtual...
call venv\Scripts\activate

echo [2/2] Arrancando el servidor web...
echo ------------------------------------------
echo El sistema ya esta disponible en:
echo http://127.0.0.1:8000/
echo ------------------------------------------
echo (Para apagar el servidor, solo cerra esta ventana)
echo.

python manage.py runserver
pause