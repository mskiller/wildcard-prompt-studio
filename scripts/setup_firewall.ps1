# scripts/setup_firewall.ps1
# Configures Windows Defender Firewall to allow local network access to Wildcard Prompt Studio

$rules = @(
    @{
        Name = "Wildcard Prompt Studio (Frontend 5173)"
        Port = 5173
    },
    @{
        Name = "Wildcard Prompt Studio (Backend 8000)"
        Port = 8000
    }
)

foreach ($r in $rules) {
    $existing = Get-NetFirewallRule -DisplayName $r.Name -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Updating firewall rule: $($r.Name)..." -ForegroundColor Cyan
        Set-NetFirewallRule -DisplayName $r.Name -Enabled True -Profile Any
    } else {
        Write-Host "Adding firewall rule: $($r.Name)..." -ForegroundColor Cyan
        New-NetFirewallRule -DisplayName $r.Name -Direction Inbound -LocalPort $r.Port -Protocol TCP -Action Allow -Profile Any
    }
}

Write-Host "`nFirewall configured successfully!" -ForegroundColor Green
Write-Host "`nYou can access Wildcard Prompt Studio from your local network using:" -ForegroundColor Yellow

$ips = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.InterfaceAlias -notlike "*Loopback*" -and
    $_.InterfaceAlias -notlike "*vEthernet*" -and
    $_.InterfaceAlias -notlike "*VMware*" -and
    $_.IPAddress -notlike "169.254*"
}

foreach ($ip in $ips) {
    Write-Host "  -> http://$($ip.IPAddress):5173 ($($ip.InterfaceAlias))" -ForegroundColor Green
}
Write-Host ""
