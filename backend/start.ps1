# SimpliFiQ Backend Startup Script
Write-Host "🛑 Stopping any existing Python processes on port 8000..." -ForegroundColor Yellow

# Kill anything on port 8000
$conn = netstat -ano | Select-String ":8000 " | Select-String "LISTENING"
if ($conn) {
    $pid = ($conn -split '\s+')[-1]
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Write-Host "  Killed PID $pid" -ForegroundColor Gray
}

Start-Sleep -Seconds 1
Write-Host "🚀 Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Cyan
python main.py
