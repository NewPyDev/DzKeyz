@echo off
:: === AUTO WEBHOOK + FLASK STARTER ===
setlocal enabledelayedexpansion

:: === YOUR TELEGRAM BOT TOKEN ===
set TOKEN=8223545849:AAGk9rL0Hz4Bepf5pyqFm1vg3qRFeGQPtoM

:: === START FLASK APP ===
start "" cmd /c "python app.py"
echo 🔥 Flask app started...

:: === START NGROK ===
start "" cmd /c "ngrok http 5000"
echo 🚀 Waiting for ngrok to start...
timeout /t 5 >nul

:: === FETCH THE NGROK URL ===
for /f "delims=" %%i in ('curl -s http://127.0.0.1:4040/api/tunnels ^| findstr "https://"') do set NGROK_URL=%%i
set NGROK_URL=%NGROK_URL:~15,-2%
echo 🌍 Found ngrok URL: %NGROK_URL%

:: === SET TELEGRAM WEBHOOK ===
curl -X POST "https://api.telegram.org/bot%TOKEN%/setWebhook" -H "Content-Type: application/json" -d "{\"url\": \"%NGROK_URL%/webhook/telegram\"}"

echo ✅ Webhook updated successfully!
echo.
echo 🛍 Your store is live at: %NGROK_URL%
pause
