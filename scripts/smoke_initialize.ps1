# =============================================================================
# smoke_initialize.ps1 — Windows PowerShell MCP smoke test
#
# Usage:
#   .\scripts\smoke_initialize.ps1                              # localhost
#   .\scripts\smoke_initialize.ps1 -BaseUrl http://host:port    # custom
#   .\scripts\smoke_initialize.ps1 -BaseUrl http://host/ltem    # proxy
# =============================================================================

param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$McpPath = "/mcp"
)

$Endpoint = "${BaseUrl}${McpPath}"
$Pass = 0
$Fail = 0

function Test-Response {
    param(
        [string]$Name,
        [string]$Response,
        [string]$Check
    )

    if ($Response -match [regex]::Escape($Check)) {
        Write-Host "  PASS " -ForegroundColor Green -NoNewline
        Write-Host $Name
        $script:Pass++
    } else {
        Write-Host "  FAIL " -ForegroundColor Red -NoNewline
        Write-Host $Name
        Write-Host "       Expected: $Check" -ForegroundColor Yellow
        Write-Host "       Got: $($Response.Substring(0, [Math]::Min(200, $Response.Length)))" -ForegroundColor Yellow
        $script:Fail++
    }
}

function Invoke-McpRequest {
    param(
        [string]$Body
    )
    try {
        $response = Invoke-RestMethod -Uri $Endpoint -Method POST `
            -ContentType "application/json" `
            -Headers @{ "Accept" = "application/json, text/event-stream" } `
            -Body $Body `
            -ErrorAction Stop
        return ($response | ConvertTo-Json -Depth 10 -Compress)
    } catch {
        return "CONNECTION_FAILED: $($_.Exception.Message)"
    }
}

Write-Host "=== LTEM MCP Server Smoke Tests (PowerShell) ===" -ForegroundColor Cyan
Write-Host "Endpoint: $Endpoint"
Write-Host ""

# ---------------------------------------------------------------------------
# Test 1: Initialize
# ---------------------------------------------------------------------------
Write-Host "1. MCP Initialize Handshake"
$initBody = @{
    jsonrpc = "2.0"
    id = 1
    method = "initialize"
    params = @{
        protocolVersion = "2024-11-05"
        capabilities = @{}
        clientInfo = @{ name = "smoke-test-ps"; version = "1.0" }
    }
} | ConvertTo-Json -Depth 5

$initResult = Invoke-McpRequest -Body $initBody
Test-Response "JSON-RPC response received" $initResult '"jsonrpc"'
Test-Response "Server info present" $initResult '"serverInfo"'

# ---------------------------------------------------------------------------
# Test 2: List Tools
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "2. List Tools"
$toolsBody = @{
    jsonrpc = "2.0"
    id = 2
    method = "tools/list"
    params = @{}
} | ConvertTo-Json -Depth 5

$toolsResult = Invoke-McpRequest -Body $toolsBody
Test-Response "Tools list returned" $toolsResult '"tools"'
Test-Response "health_check present" $toolsResult "health_check"

# ---------------------------------------------------------------------------
# Test 3: Health Check
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "3. Health Check Tool"
$healthBody = @{
    jsonrpc = "2.0"
    id = 3
    method = "tools/call"
    params = @{
        name = "health_check"
        arguments = @{}
    }
} | ConvertTo-Json -Depth 5

$healthResult = Invoke-McpRequest -Body $healthBody
Test-Response "Health check responded" $healthResult '"result"'

# ---------------------------------------------------------------------------
# Test 4: List Tables
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "4. List Tables Tool"
$tablesBody = @{
    jsonrpc = "2.0"
    id = 4
    method = "tools/call"
    params = @{
        name = "list_tables"
        arguments = @{}
    }
} | ConvertTo-Json -Depth 5

$tablesResult = Invoke-McpRequest -Body $tablesBody
Test-Response "Tables list responded" $tablesResult '"result"'

# ---------------------------------------------------------------------------
# Test 5: Get Regions
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "5. Get Regions Tool"
$regionsBody = @{
    jsonrpc = "2.0"
    id = 5
    method = "tools/call"
    params = @{
        name = "get_regions"
        arguments = @{}
    }
} | ConvertTo-Json -Depth 5

$regionsResult = Invoke-McpRequest -Body $regionsBody
Test-Response "Regions responded" $regionsResult '"result"'

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Results: $Pass passed, $Fail failed ===" -ForegroundColor Cyan

if ($Fail -gt 0) {
    Write-Host "Some tests failed. Check the endpoint and server logs." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "All smoke tests passed!" -ForegroundColor Green
    exit 0
}
