# Save Teams webhook URL to backend/.env and optionally send a test message.
# Usage:
#   .\scripts\set_teams_webhook.ps1 -Url "https://outlook.office.com/webhook/..."
#   .\scripts\set_teams_webhook.ps1 -Url "https://..." -Test

param(
    [Parameter(Mandatory = $true)]
    [string]$Url,
    [switch]$Test
)

$ErrorActionPreference = "Stop"
$envFile = Join-Path $PSScriptRoot ".." ".env" | Resolve-Path
$content = Get-Content $envFile -Raw

if ($content -match "(?m)^TEAMS_WEBHOOK_URL=.*$") {
    $content = $content -replace "(?m)^TEAMS_WEBHOOK_URL=.*$", "TEAMS_WEBHOOK_URL=$Url"
} else {
    $content += "`nTEAMS_WEBHOOK_URL=$Url`n"
}

Set-Content -Path $envFile -Value $content -NoNewline
Write-Host "Updated TEAMS_WEBHOOK_URL in .env"

if ($Test) {
    Write-Host "Sending test message (backend must be running on port 8000)..."
    $body = @{ url = $Url } | ConvertTo-Json
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/system/test-teams-webhook" -Method POST -Body $body -ContentType "application/json"
        Write-Host "SUCCESS:" ($resp | ConvertTo-Json -Compress)
    } catch {
        Write-Host "Test failed. Restart backend after .env change, then run:"
        Write-Host "  Invoke-RestMethod -Uri http://127.0.0.1:8000/api/system/test-teams-webhook -Method POST"
    }
} else {
    Write-Host "Restart backend (Ctrl+C -> .\run.ps1), then test with:"
    Write-Host "  .\scripts\set_teams_webhook.ps1 -Url `"$Url`" -Test"
}
