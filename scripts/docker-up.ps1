param(
    [int]$StartPort = 8080,
    [switch]$Detached
)

function Test-PortInUse {
    param([int]$Port)

    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $connection
}

$port = $StartPort
while (Test-PortInUse -Port $port) {
    $port += 1
}

$env:APP_PORT = [string]$port
Write-Host "Using APP_PORT=$env:APP_PORT"

if ($Detached) {
    docker compose up --build -d
} else {
    docker compose up --build
}
