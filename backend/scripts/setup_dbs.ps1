param(
    [string]$DevDbUrl = 'sqlite:///./dietapp_dev.db',
    [string]$TestDbUrl = 'sqlite:///./dietapp_test.db'
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $env:PYTHONPATH = '.'

    if (Test-Path 'dietapp_dev.db') { Remove-Item 'dietapp_dev.db' -Force }
    if (Test-Path 'dietapp_test.db') { Remove-Item 'dietapp_test.db' -Force }

    $env:DATABASE_URL = $DevDbUrl
    alembic upgrade head

    $env:DATABASE_URL = $TestDbUrl
    alembic upgrade head

    Write-Output "Provisioned dev DB:  $DevDbUrl"
    Write-Output "Provisioned test DB: $TestDbUrl"
}
finally {
    Pop-Location
}
