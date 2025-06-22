@echo off
title PC İzleme Sistemi - Sunucu
cls
echo -------------------------------------------------
echo     PC İzleme Sistemi Sunucu Başlatılıyor
echo -------------------------------------------------
echo.

echo Soket sunucusu başlatılıyor...
start "Socket Server - Port 5002" cmd /k "python socket_server.py"

echo Flask web uygulaması başlatılıyor...
python app.py

pause 