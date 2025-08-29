@echo off
REM start_fluxon.bat
echo 🚀 Iniciando Sistema Fluxon Quantum...
echo ======================================

REM Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM 1. Inicia o Flask em background
echo 📦 Iniciando servidor Flask...
start "Flask Server" python server\app.py

REM Aguarda o Flask inicializar
echo ⏳ Aguardando inicialização do Flask...
timeout /t 8 /nobreak >nul

REM 2. Inicia o NgrokManager
echo 🌐 Iniciando monitor Ngrok...
start "Ngrok Manager" python server\ngrok_manager.py

REM Aguarda o Ngrok inicializar
echo ⏳ Aguardando inicialização do Ngrok...
timeout /t 5 /nobreak >nul

REM 3. Inicia o Proxy Server (CORRIGIDO: está em server/services/)
echo 🔗 Iniciando Proxy Server...
start "Proxy Server" python server\services\proxy_server.py

REM 4. Verifica se o monitor do sistema existe
echo 📊 Verificando monitor do sistema...
if exist server\system_monitor.py (
    start "System Monitor" python server\system_monitor.py
) else (
    echo ℹ️  Monitor do sistema não encontrado, continuando...
)

echo ✅ Sistema Fluxon iniciado!
echo 💡 Acesse: http://localhost:5000  (CORRIGIDO: porta 5000 do Flask)
echo 📊 Flask: http://localhost:5000
echo 🌐 Ngrok Manager em execução
echo ======================================
echo Use o Gerenciador de Tarefas para parar os processos
echo ou feche esta janela para continuar com os processos em execução
pause