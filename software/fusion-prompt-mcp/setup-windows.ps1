$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
py -3 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.10+ and retry.' }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$serverPath = Join-Path $PSScriptRoot 'server.py'
$config = "[mcp_servers.fusion]`ncommand = '$pythonPath'`nargs = ['$serverPath']`ntool_timeout_sec = 45`n"
$config | Set-Content -Encoding utf8 'mcp-client-config.generated.toml'
Write-Host 'Setup complete. Follow README.md to load the Fusion add-in and register the MCP.'
