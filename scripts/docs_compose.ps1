param(
    [string]$Port = "8080"
)

$ErrorActionPreference = "Stop"
$env:DOCS_PORT = $Port
docker compose -f compose.docs.yml up --build
