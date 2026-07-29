# Start the FastAPI backend (uses venv at C:\Users\akula\venv\coord-engine)
$VenvPython = "C:\Users\akula\venv\coord-engine\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating venv at C:\Users\akula\venv\coord-engine ..."
    python -m venv "C:\Users\akula\venv\coord-engine"
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r requirements.txt
}

# Kill any stale/hung server still holding port 8000
Write-Host "Clearing port 8000 ..."
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { if ($_ -gt 0) { taskkill /PID $_ /F 2>$null } }
Start-Sleep -Seconds 2

Set-Location $PSScriptRoot
Write-Host "Starting backend on http://127.0.0.1:8000 ..."
Write-Host "Press Ctrl+C to stop."
& $VenvPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
