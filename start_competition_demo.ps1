Write-Host "===================================================" -ForegroundColor Green
Write-Host "🍄 MYCELIUM NETWORK - COMPETITION BOOTSTRAP 🍄" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""

Write-Host "🧹 Cleaning up previous instances (closing old ports)..." -ForegroundColor Yellow
$ports = 8000, 8010, 8011, 8012, 8013, 8014, 5173
foreach ($p in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
    if ($conn) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 2
Write-Host ""

Write-Host "[1/3] Booting Mycelium Registry Server (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"python -m server.app`""

Start-Sleep -Seconds 5

Write-Host "[2/3] Spinning up Real-World Agents..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"python examples/real_agents/real_weather_agent.py`""
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"python examples/real_agents/real_translator_agent.py`""
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"python examples/real_agents/real_crypto_agent.py`""
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"python examples/real_agents/real_wikipedia_agent.py`""
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -Command `"python examples/real_agents/real_currency_agent.py`""

Start-Sleep -Seconds 4

Write-Host "[3/3] Launching Spatial Dashboard in Web Browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "✅ ALL SYSTEMS GO! LIVE UI IS OPENING." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""
Write-Host "NOTE: To trigger the automated background chains, run:" -ForegroundColor Yellow
Write-Host "python scripts/real_world_demo.py" -ForegroundColor Yellow
Write-Host ""
