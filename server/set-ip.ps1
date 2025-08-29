# set-ip-simple.ps1 - Configuração simplificada de IP
$IPAddress = "192.168.99.170"
$SubnetMask = "255.255.255.0"
$DefaultGateway = "192.168.99.241"
$DNSServers = @("8.8.8.8", "8.8.4.4")
$InterfaceAlias = "Ethernet 3"

# Verificar se é admin
$admin = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($admin)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Execute como Administrador!"
    exit
}

try {
    Write-Host "Configurando IP estático..."
    
    # Remover config antiga
    Remove-NetIPAddress -InterfaceAlias $InterfaceAlias -Confirm:$false -ErrorAction SilentlyContinue
    Remove-NetRoute -InterfaceAlias $InterfaceAlias -Confirm:$false -ErrorAction SilentlyContinue
    
    # Configurar novo IP
    New-NetIPAddress -InterfaceAlias $InterfaceAlias -IPAddress $IPAddress -PrefixLength 24 -DefaultGateway $DefaultGateway
    
    # Configurar DNS
    Set-DnsClientServerAddress -InterfaceAlias $InterfaceAlias -ServerAddresses $DNSServers
    
    Write-Host "Configuracao concluida!"
    Write-Host "IP: $IPAddress"
    Write-Host "Gateway: $DefaultGateway"
    Write-Host "DNS: $($DNSServers -join ', ')"
    
} catch {
    Write-Host "Erro: $($_.Exception.Message)"
}