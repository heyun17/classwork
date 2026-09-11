# ==========================================
# Network Connection Restart Test
# 1. Disconnect network
# 2. Wait 10 seconds
# 3. Reconnect network
# 4. Check connection with ping
# ==========================================

# Find the first active network adapter
$adapter = Get-NetAdapter |
    Where-Object { $_.Status -eq "Up" } |
    Select-Object -First 1

# Exit if no active adapter is found
if (-not $adapter) {
    Write-Host "No active network adapter was found."
    exit
}

Write-Host "Network adapter: $($adapter.Name)"
Write-Host ""

# -----------------------------
# 1. Disconnect network
# -----------------------------
Write-Host "Disconnecting network..."

Disable-NetAdapter `
    -Name $adapter.Name `
    -Confirm:$false

# -----------------------------
# 2. Wait 10 seconds
# -----------------------------
Write-Host "Waiting for 10 seconds..."

Start-Sleep -Seconds 10

# -----------------------------
# 3. Reconnect network
# -----------------------------
Write-Host "Reconnecting network..."

Enable-NetAdapter `
    -Name $adapter.Name `
    -Confirm:$false

# Wait for the network connection to recover
Write-Host "Waiting for network connection..."

Start-Sleep -Seconds 5

# -----------------------------
# 4. Check network connection
# -----------------------------
Write-Host ""
Write-Host "Checking network connection..."

$pingResult = Test-Connection `
    -ComputerName "8.8.8.8" `
    -Count 2 `
    -Quiet

if ($pingResult) {
    Write-Host "Network connection is working."
}
else {
    Write-Host "Network connection failed."
}