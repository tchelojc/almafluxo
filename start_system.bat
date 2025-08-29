@echo off
echo ========================================
echo   🚀 INICIANDO SISTEMA ALMA COMPLETO
echo ========================================

echo 1. Iniciando Flask Server (5000)...
start "Flask Server" cmd /k "cd server && python app.py"

echo Aguardando Flask iniciar...
timeout /t 5 /nobreak

echo 2. Iniciando Streamlit Hub (8501)...
start "Streamlit Hub" cmd /k "cd server\scripts\seletor && streamlit run seletor.py --server.port=8501"

echo 3. Iniciando Proxy Server (5500)...
start "Proxy Server" cmd /k "cd server\services && python proxy_server.py"

echo ========================================
echo ✅ Todos os servidores iniciados!
echo 🌐 Acesse: http://localhost:5500
echo ========================================
pause