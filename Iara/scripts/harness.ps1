[CmdletBinding()]
param(
    [ValidateSet('setup', 'harness', 'context', 'backend', 'frontend', 'e2e', 'docker-up', 'docker-e2e', 'docker-down', 'all')]
    [string]$Target = 'all'
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backend = Join-Path $root 'Backend'
$frontend = Join-Path $root 'Frontend'
$venv = Join-Path $backend '.venv'
$python = Join-Path $venv 'Scripts/python.exe'
$venvScripts = Join-Path $venv 'Scripts'
$composeBase = @('-p', 'iara', '-f', (Join-Path $root 'compose.yaml'))
$composeDesenvolvimento = @($composeBase + @('-f', (Join-Path $root 'compose.dev.yaml')))
$composeTeste = @('-p', 'iara-e2e', '-f', (Join-Path $root 'compose.yaml'), '-f', (Join-Path $root 'compose.test.yaml'))

function Invoke-Checked {
    param([string]$Name, [scriptblock]$Action)
    Write-Host ''
    Write-Host "== $Name ==" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Name falhou com codigo $LASTEXITCODE"
    }
}

function Invoke-Backend {
    if (-not (Test-Path $python)) {
        throw "Ambiente Python nao encontrado. Execute: .\scripts\harness.ps1 -Target setup"
    }
    Push-Location $backend
    try {
        Invoke-Checked 'Ruff' { & $python -m ruff check app tests }
        Invoke-Checked 'Pytest com cobertura' { & $python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=80 }
    }
    finally {
        Pop-Location
    }
}

function Invoke-Harness {
    $validator = Join-Path $root 'scripts\validate-harness.py'
    if (Test-Path $python) {
        Invoke-Checked 'Validar Harness' { & $python $validator }
    }
    else {
        Invoke-Checked 'Validar Harness' { py -3 $validator }
    }
}

function Invoke-Context {
    Push-Location $root
    try {
        if (Test-Path $python) {
            Invoke-Checked 'Testes de retrieval e montagem de contexto' { & $python -m unittest discover -s harness/context -p 'test_*.py' }
        }
        else {
            Invoke-Checked 'Testes de retrieval e montagem de contexto' { py -3 -m unittest discover -s harness/context -p 'test_*.py' }
        }
    }
    finally {
        Pop-Location
    }
}

function Invoke-Frontend {
    if (-not (Test-Path (Join-Path $frontend 'node_modules'))) {
        throw "Dependencias Node nao encontradas. Execute: .\scripts\harness.ps1 -Target setup"
    }
    Push-Location $frontend
    try {
        Invoke-Checked 'Lint, tipos, unit tests e build' { npm run check }
    }
    finally {
        Pop-Location
    }
}

function Invoke-E2E {
    if (-not (Test-Path $python)) {
        throw "Ambiente Python nao encontrado. Execute: .\scripts\harness.ps1 -Target setup"
    }
    $oldPath = $env:PATH
    try {
        $env:PATH = "$venvScripts;$oldPath"
        Push-Location $frontend
        try {
            Invoke-Checked 'Smoke integrado Playwright' { npm run test:e2e }
        }
        finally {
            Pop-Location
        }
    }
    finally {
        $env:PATH = $oldPath
    }
}

function Assert-DockerCompose {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker CLI nao encontrado. Instale/inicie Docker Desktop e habilite Docker Compose v2.24 ou superior.'
    }
    $versaoCompose = & docker compose version --short
    if ($LASTEXITCODE -ne 0) {
        throw 'Docker Compose v2 nao esta disponivel. Inicie Docker Desktop e tente novamente.'
    }
    $correspondenciaVersao = [regex]::Match(($versaoCompose -join ' '), '(\d+\.\d+\.\d+)')
    if (-not $correspondenciaVersao.Success -or [version]$correspondenciaVersao.Groups[1].Value -lt [version]'2.24.0') {
        throw "Docker Compose v2.24 ou superior e necessario; versao encontrada: $versaoCompose"
    }
    & docker info --format '{{.ServerVersion}}' *> $null
    if ($LASTEXITCODE -ne 0) {
        throw 'O Docker Engine nao esta ativo. Inicie o Docker Desktop e execute novamente o alvo Docker.'
    }
}

function Invoke-DockerUp {
    Assert-DockerCompose
    Invoke-Checked 'Validar Compose de desenvolvimento' { & docker compose @composeDesenvolvimento config --quiet }
    Invoke-Checked 'Iniciar Backend e Frontend locais' {
        & docker compose @composeDesenvolvimento up --build --detach --wait
    }
    $portaFrontend = if ($env:IARA_FRONTEND_PORT) { $env:IARA_FRONTEND_PORT } else { '5173' }
    Write-Host "Iara pronta em http://localhost:$portaFrontend. A API fica acessivel pelo proxy local do Frontend." -ForegroundColor Green
}

function Invoke-DockerE2E {
    Assert-DockerCompose
    $argumentos = @($composeTeste + @('--profile', 'test'))
    Invoke-Checked 'Validar Compose isolado de testes' { & docker compose @argumentos config --quiet }

    $codigoTeste = 0
    $codigoLimpeza = 0
    try {
        & docker compose @argumentos up --build --abort-on-container-exit --exit-code-from e2e e2e
        $codigoTeste = $LASTEXITCODE
    }
    finally {
        & docker compose @argumentos down --volumes --remove-orphans
        $codigoLimpeza = $LASTEXITCODE
    }

    if ($codigoTeste -ne 0) {
        throw "Smoke integrado no Docker falhou com codigo $codigoTeste"
    }
    if ($codigoLimpeza -ne 0) {
        throw "A limpeza do projeto isolado iara-e2e falhou com codigo $codigoLimpeza"
    }
}

function Invoke-DockerDown {
    Assert-DockerCompose
    Invoke-Checked 'Parar servicos locais sem remover o SQLite persistente' {
        & docker compose @composeDesenvolvimento down
    }
}

switch ($Target) {
    'setup' {
        if (-not (Test-Path $python)) {
            Invoke-Checked 'Criar ambiente Python 3' { py -3 -m venv $venv }
        }
        Invoke-Checked 'Instalar backend e ferramentas de teste' {
            Push-Location $backend
            try {
                & $python -m pip install -r .\requirements.lock.txt
                if ($LASTEXITCODE -ne 0) { throw 'Instalacao das dependencias travadas falhou' }
                & $python -m pip install --no-deps -e .
            } finally { Pop-Location }
        }
        Invoke-Checked 'Instalar frontend com lockfile' {
            Push-Location $frontend
            try { npm ci } finally { Pop-Location }
        }
        Invoke-Checked 'Instalar Chromium do Playwright' {
            Push-Location $frontend
            try { npx playwright install chromium } finally { Pop-Location }
        }
    }
    'harness' { Invoke-Harness }
    'context' { Invoke-Context }
    'backend' { Invoke-Backend }
    'frontend' { Invoke-Frontend }
    'e2e' { Invoke-E2E }
    'docker-up' { Invoke-DockerUp }
    'docker-e2e' { Invoke-DockerE2E }
    'docker-down' { Invoke-DockerDown }
    'all' {
        Invoke-Harness
        Invoke-Context
        Invoke-Backend
        Invoke-Frontend
        Invoke-E2E
    }
}
