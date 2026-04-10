$ErrorActionPreference = "Stop"

$composeArgs = @(
    "-f", "server/infrastructure/docker/docker-compose.yml",
    "--env-file", "server/.env"
)

Write-Host "[1/4] Stopping stack and removing volumes..."
docker compose @composeArgs down -v --remove-orphans

Write-Host "[2/4] Rebuilding and starting stack..."
docker compose @composeArgs up -d --build

Write-Host "[3/4] Waiting for API healthz..."
$ok = $false
for ($i = 1; $i -le 60; $i++) {
    try {
        $resp = curl.exe -sS http://localhost:8000/healthz
        if ($resp -match '"ok"\s*:\s*true') {
            $ok = $true
            Write-Host "API is healthy: $resp"
            break
        }
    }
    catch {
    }
    Start-Sleep -Seconds 2
}

if (-not $ok) {
    Write-Host "ERROR: API healthcheck failed after reset."
    Write-Host "---- API logs (tail 200) ----"
    docker compose @composeArgs logs --tail 200 api
    Write-Host "---- PostgreSQL logs (tail 200) ----"
    docker compose @composeArgs logs --tail 200 postgres
    exit 1
}

Write-Host "[4/4] Done."
