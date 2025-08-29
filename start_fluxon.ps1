# start_fluxon.ps1 - SCRIPT CORRIGIDO
Write-Host "🚀 Iniciando Sistema Fluxon Quantum..." -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Definir diretório base correto
$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "📁 Diretório base: $baseDir" -ForegroundColor Yellow

# Ativar ambiente virtual
Write-Host "🔧 Ativando ambiente virtual..." -ForegroundColor Yellow
$venvPath = Join-Path $baseDir "venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "✅ Ambiente virtual ativado" -ForegroundColor Green
} else {
    Write-Host "⚠️  Ambiente virtual não encontrado em: $venvPath" -ForegroundColor Red
    Write-Host "ℹ️  Continuando sem ambiente virtual..." -ForegroundColor Yellow
}

# Função auxiliar para iniciar serviços
function Start-ServiceProcess($name, $scriptPath) {
    Write-Host "▶️  Iniciando $name..." -ForegroundColor Yellow
    Write-Host "📋 Script: $scriptPath" -ForegroundColor Gray
    
    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ Arquivo não encontrado: $scriptPath" -ForegroundColor Red
        return $null
    }
    
    try {
        $process = Start-Process -FilePath "python" -ArgumentList "`"$scriptPath`"" -PassThru -WindowStyle Hidden
        Write-Host "✅ $name iniciado (PID: $($process.Id))" -ForegroundColor Green
        Start-Sleep -Seconds 2
        return $process
    } catch {
        Write-Host "❌ Erro ao iniciar $name`: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 1. Inicia Flask
$flaskPath = Join-Path $baseDir "server\app.py"
$flaskProcess = Start-ServiceProcess "Flask Server" $flaskPath
if ($flaskProcess) {
    Write-Host "⏳ Aguardando inicialização do Flask..." -ForegroundColor Yellow
    Start-Sleep -Seconds 8
}

# 2. Inicia Ngrok Manager
$ngrokPath = Join-Path $baseDir "server\ngrok_manager.py"
$ngrokProcess = Start-ServiceProcess "Ngrok Manager" $ngrokPath
if ($ngrokProcess) {
    Write-Host "⏳ Aguardando inicialização do Ngrok..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# 3. Inicia Proxy Server (CORRIGIDO: caminho correto)
$proxyPath = Join-Path $baseDir "server\services\proxy_server.py"
$proxyProcess = Start-ServiceProcess "Proxy Server" $proxyPath

# 4. Inicia Monitor do sistema (se existir)
$monitorProcess = $null
$monitorPath = Join-Path $baseDir "server\system_monitor.py"
if (Test-Path $monitorPath) {
    $monitorProcess = Start-ServiceProcess "System Monitor" $monitorPath
} else {
    Write-Host "ℹ️  Monitor do sistema não encontrado: $monitorPath" -ForegroundColor Yellow
}

Write-Host "`n✅ Sistema Fluxon iniciado!" -ForegroundColor Green
Write-Host "💡 Acesse: http://localhost:5000" -ForegroundColor Cyan
Write-Host "📊 Flask: http://localhost:5000" -ForegroundColor Cyan
Write-Host "🌐 Ngrok Manager em execução" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Green

Write-Host "Processos iniciados:" -ForegroundColor Yellow
if ($flaskProcess)   { Write-Host "• Flask Server (PID: $($flaskProcess.Id))" -ForegroundColor White }
if ($ngrokProcess)   { Write-Host "• Ngrok Manager (PID: $($ngrokProcess.Id))" -ForegroundColor White }
if ($proxyProcess)   { Write-Host "• Proxy Server (PID: $($proxyProcess.Id))" -ForegroundColor White }
if ($monitorProcess) { Write-Host "• System Monitor (PID: $($monitorProcess.Id))" -ForegroundColor White }

Write-Host "======================================" -ForegroundColor Green
Write-Host "Para parar todos os serviços, execute:" -ForegroundColor Red
if ($flaskProcess -and $ngrokProcess -and $proxyProcess) {
    Write-Host "Stop-Process -Id $($flaskProcess.Id), $($ngrokProcess.Id), $($proxyProcess.Id)" -ForegroundColor Red
}
Write-Host "Ou use: Get-Process -Name 'python' | Where-Object {`$_.Path -like '*flux_on*'} | Stop-Process" -ForegroundColor Red
Write-Host "`nOu feche esta janela para manter os serviços rodando" -ForegroundColor Yellow

# Script para parar processos
$stopScript = @'
Get-Process -Name "python" -ErrorAction SilentlyContinue | 
Where-Object { $_.Path -like "*flux_on*" } | 
Stop-Process -Force
Write-Host "✅ Processos do Fluxon parados" -ForegroundColor Green
'@
$stopScript | Out-File -FilePath (Join-Path $baseDir "stop_fluxon.ps1") -Encoding UTF8
Write-Host "📝 Script de parada criado: stop_fluxon.ps1" -ForegroundColor Cyan

# Mantém a janela aberta
Write-Host "`nPressione Enter para sair (os serviços continuarão rodando)" -ForegroundColor Yellow
Read-Host