
$ports = 5173, 5174, 8000
foreach ($port in $ports) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { 
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        Write-Output "Killed PID $_ on port $port" 
    }
}
taskkill /F /IM node.exe /T 2>$null
Write-Output "Cleanup Complete"
