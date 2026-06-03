# LTEM Database MCP Server — Windows Launcher (PowerShell)
# Run from the repo root: .\scripts\run_mcp.ps1

$ErrorActionPreference = "Stop"

# Resolve repo root (parent of scripts/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

Push-Location $RepoRoot
try {
	# Check .env exists
	if (-not (Test-Path ".env")) {
		Write-Error @"
.env file not found in $RepoRoot
Copy .env.example to .env and fill in credentials:
  cp .env.example .env
"@
		exit 1
	}

	# Check required env vars by parsing .env
	$envContent = Get-Content ".env" -Raw
	if ($envContent -notmatch "LTEM_DB_PASSWORD" -or $envContent -match "CHANGEME") {
		Write-Error @"
LTEM_DB_PASSWORD is missing or still set to CHANGEME.
Edit .env and set the actual database password.
"@
		exit 1
	}

	# Check fastmcp is available
	$fastmcp = Get-Command fastmcp -ErrorAction SilentlyContinue
	if (-not $fastmcp) {
		# Try python -m fastmcp as fallback
		Write-Warning "fastmcp not found in PATH. Trying 'python -m fastmcp'..."
		python -m fastmcp run mcp_server/server.py:mcp --transport stdio
	} else {
		fastmcp run mcp_server/server.py:mcp --transport stdio
	}
} finally {
	Pop-Location
}
