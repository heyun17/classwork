Write-Host "===== 내 컴퓨터 ====="
Get-Date
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model