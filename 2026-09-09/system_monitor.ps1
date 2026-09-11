# ===== 1. 정보 수집 =====

$pc = Get-CimInstance Win32_ComputerSystem                         # 제조사, 모델, 메모리 정보를 가져온다.
$os = Get-CimInstance Win32_OperatingSystem                        # 운영체제와 최근 부팅 정보를 가져온다.
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1    # CPU 정보를 가져온다.
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"  # C드라이브 정보를 가져온다.


# ===== 2. 계산 =====

$totalRam = $pc.TotalPhysicalMemory / 1GB                          # 전체 메모리를 GB로 바꾼다.
$freeRam = $os.FreePhysicalMemory * 1KB / 1GB                      # 남은 메모리를 GB로 바꾼다.
$usedRam = $totalRam - $freeRam                                   # 사용 중인 메모리를 계산한다.
$ramPercent = ($usedRam / $totalRam) * 100                         # 메모리 사용률을 계산한다.

$totalDisk = $disk.Size / 1GB                                     # C드라이브 전체 용량을 GB로 바꾼다.
$freeDisk = $disk.FreeSpace / 1GB                                 # C드라이브 남은 공간을 GB로 바꾼다.
$usedDisk = $totalDisk - $freeDisk                                # C드라이브 사용량을 계산한다.


# ===== 3. 출력 =====

Write-Host "===== 내 PC 시스템 정보 ====="                         # 제목을 출력한다.
Write-Host "제조사/모델 : $($pc.Manufacturer) / $($pc.Model)"      # 제조사와 모델명을 출력한다.
Write-Host "운영체제    : $($os.Caption)"                          # 운영체제 이름을 출력한다.
Write-Host "CPU         : $($cpu.Name)"                            # CPU 이름을 출력한다.
Write-Host "CPU 코어    : $($cpu.NumberOfCores)개"                 # CPU 물리 코어 수를 출력한다.

Write-Host "메모리      : $([math]::Round($usedRam,1)) / $([math]::Round($totalRam,1)) GB ($([math]::Round($ramPercent,1))%)"  # 메모리 상태를 출력한다.

Write-Host "C드라이브   : 사용 $([math]::Round($usedDisk,1)) / 전체 $([math]::Round($totalDisk,1)) GB / 남음 $([math]::Round($freeDisk,1)) GB"  # 디스크 상태를 출력한다.

Write-Host "최근 부팅   : $($os.LastBootUpTime)"                   # 최근 부팅 시각을 출력한다.