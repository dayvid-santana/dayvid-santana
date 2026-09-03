# Sobe a assistente completa: dev-agent (Agents), devmate serve (Cortana/chat) e o
# frontend Diana. Rode a partir de qualquer diretorio: `powershell -File start.ps1`.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "Iniciando dev-agent (Agents, 127.0.0.1:8765)..." -ForegroundColor Cyan
dev-agent start

Write-Host "Iniciando devmate serve (Cortana, 127.0.0.1:8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\Cortana'; .\.venv\Scripts\Activate.ps1; devmate serve"
)

Write-Host "Iniciando Diana (frontend, http://localhost:5174)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\Diana'; npm run dev"
)

Write-Host "Pronto. Abra http://localhost:5174 quando o Diana terminar de subir." -ForegroundColor Green
