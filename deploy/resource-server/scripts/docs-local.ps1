param([string]$Port = "8080")

$ErrorActionPreference = "Stop"
$env:DOCS_PORT = $Port
$compose = Join-Path $PSScriptRoot "..\compose.local.yml"
docker compose -f $compose up --build docs
