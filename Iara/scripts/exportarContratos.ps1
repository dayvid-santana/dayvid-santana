# Iara - distribuição dos contratos compartilhados
# Data: 19/11/2026
# Objetivo: Copiar os schemas canônicos versionados para o workspace Backend/Frontend.

<#
.SYNOPSIS
Exporta os schemas compartilhados da Iara para a raiz do workspace.

.DESCRIPTION
Os schemas canônicos pertencem a `Iara/contracts` neste repositório. O Backend e o
Frontend usam uma cópia comum em `<workspaceRoot>/contracts`, fora dos respectivos
checkouts. Este script valida o JSON, copia os quatro schemas e confirma os hashes.

.PARAMETER workspaceRoot
Raiz existente que contém os diretórios `Iara-Backend` e `Iara-Frontend`.
Informe explicitamente a raiz do workspace compartilhado.

.OUTPUTS
Imprime a revisão Git da fonte e o SHA-256 de cada arquivo exportado.

.EXAMPLE
./Iara/scripts/exportarContratos.ps1 -workspaceRoot 'C:/projects/Iara'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Container })]
    [string]$workspaceRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Localiza o repositório que contém a fonte canônica dos schemas.
$repositoryRoot = (& git -C $PSScriptRoot rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) {
    throw 'Não foi possível identificar o repositório Git da fonte canônica.'
}

$sourceContracts = Join-Path $PSScriptRoot '..\contracts'
$sourceContracts = (Resolve-Path -LiteralPath $sourceContracts).Path
$resolvedWorkspaceRoot = (Resolve-Path -LiteralPath $workspaceRoot).Path
$destinationContracts = Join-Path $resolvedWorkspaceRoot 'contracts'

if (-not (Test-Path -LiteralPath (Join-Path $resolvedWorkspaceRoot 'Iara-Backend') -PathType Container)) {
    throw "O workspace não contém Iara-Backend: $resolvedWorkspaceRoot"
}
if (-not (Test-Path -LiteralPath (Join-Path $resolvedWorkspaceRoot 'Iara-Frontend') -PathType Container)) {
    throw "O workspace não contém Iara-Frontend: $resolvedWorkspaceRoot"
}

# Registra a revisão para permitir reproduzir exatamente a fonte exportada.
$sourceRevision = (& git -C $repositoryRoot rev-parse --short HEAD).Trim()
if ($LASTEXITCODE -ne 0) {
    throw 'Não foi possível identificar a revisão Git da fonte canônica.'
}

$schemaFiles = @(
    'eventos-sse-v1.schema.json',
    'eventos-sse-v2.schema.json',
    'mensagem-v1.schema.json',
    'mensagem-v2.schema.json'
)

if (-not (Test-Path -LiteralPath $destinationContracts -PathType Container)) {
    New-Item -ItemType Directory -Path $destinationContracts | Out-Null
}

Write-Host "Fonte canônica: $repositoryRoot (revisão $sourceRevision)"
foreach ($schemaFile in $schemaFiles) {
    $sourceFile = Join-Path $sourceContracts $schemaFile
    $destinationFile = Join-Path $destinationContracts $schemaFile
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "Schema canônico ausente: $sourceFile"
    }

    # Recusa arquivos que não sejam JSON válido antes de atualizar a cópia comum.
    Get-Content -LiteralPath $sourceFile -Raw -Encoding utf8 |
        ConvertFrom-Json -ErrorAction Stop | Out-Null

    Copy-Item -LiteralPath $sourceFile -Destination $destinationFile -Force
    $sourceHash = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash
    $destinationHash = (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash
    if ($sourceHash -ne $destinationHash) {
        throw "O hash exportado diverge da origem: $schemaFile"
    }

    Write-Host "$schemaFile SHA-256 $destinationHash"
}
