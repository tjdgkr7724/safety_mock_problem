$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Set-Location -LiteralPath $projectRoot

function Find-Python {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:ProgramFiles\Python313\python.exe"
    )
    foreach ($registryPath in @('HKCU:\Software\Python\PythonCore\3.13\InstallPath', 'HKLM:\Software\Python\PythonCore\3.13\InstallPath')) {
        if (Test-Path -LiteralPath $registryPath) {
            $installPath = (Get-Item -LiteralPath $registryPath).GetValue('')
            if ($installPath) { $candidates += Join-Path $installPath 'python.exe' }
        }
    }
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        try {
            $detected = & $launcher.Source -3.13 -c 'import sys; print(sys.executable)' 2>$null
            if ($LASTEXITCODE -eq 0 -and $detected) { $candidates += $detected }
        } catch { } # A launcher can exist without Python 3.13 installed.
    }
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            & $candidate -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3,13) else 1)' 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        }
    }
    return $null
}

function Install-PackageWithWinget([string]$package) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) { throw 'winget이 없습니다. Microsoft Store에서 앱 설치 관리자를 설치한 뒤 다시 실행하세요.' }
    & $winget.Source install --id $package --exact --source winget --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) { throw "$package 설치에 실패했거나 취소되었습니다. 인터넷 연결과 설치 창을 확인하세요." }
}

function Test-WebView2 {
    $roots = @('HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients', 'HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients', 'HKCU:\SOFTWARE\Microsoft\EdgeUpdate\Clients')
    foreach ($registryRoot in $roots) {
        if (Test-Path -LiteralPath $registryRoot) {
            foreach ($key in Get-ChildItem -LiteralPath $registryRoot) {
                $info = Get-ItemProperty -LiteralPath $key.PSPath
                if ($info.name -like '*WebView2*' -and $info.pv -and $info.pv -ne '0.0.0.0') { return $true }
            }
        }
    }
    return $false
}

try {
    Write-Host '[1/4] Python 확인 중...'
    $pythonPath = Find-Python
    if (-not $pythonPath) {
        Write-Host 'Python 3.13을 설치합니다. 설치 안내가 나타나면 완료해 주세요.'
        Install-PackageWithWinget 'Python.Python.3.13'
        $pythonPath = Find-Python
        if (-not $pythonPath) { throw 'Python 설치 경로를 찾지 못했습니다. 실행 파일을 닫고 다시 더블클릭하세요.' }
    }

    Write-Host '[2/4] 전용 실행환경 준비 중...'
    # Separate from the developer venv; it is never copied to another PC.
    $runtimeRoot = Join-Path $projectRoot '.launcher-venv'
    $runtimePython = Join-Path $runtimeRoot 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $runtimePython)) {
        & $pythonPath -m venv $runtimeRoot
        if ($LASTEXITCODE -ne 0) { throw '가상환경 생성 실패. 압축을 모두 풀고 쓰기 가능한 폴더에서 실행하세요.' }
    }
    $requirementsPath = Join-Path $projectRoot 'requirements-launcher.txt'
    $requirementsHash = (Get-FileHash -LiteralPath $requirementsPath).Hash + (Get-FileHash -LiteralPath (Join-Path $projectRoot 'requirements.txt')).Hash
    $stamp = Join-Path $runtimeRoot 'requirements.sha256'
    $installedHash = if (Test-Path -LiteralPath $stamp) { (Get-Content -LiteralPath $stamp -Raw).Trim() } else { '' }
    if ($installedHash -ne $requirementsHash) {
        & $runtimePython -m pip install -r $requirementsPath
        if ($LASTEXITCODE -ne 0) { throw '패키지 설치 실패. 인터넷 연결을 확인한 뒤 다시 실행하세요.' }
        Set-Content -LiteralPath $stamp -Value $requirementsHash -Encoding ASCII
    }

    Write-Host '[3/4] 화면 실행 구성 확인 중...'
    if (-not (Test-WebView2)) {
        Write-Host 'Microsoft Edge WebView2 Runtime을 설치합니다.'
        Install-PackageWithWinget 'Microsoft.EdgeWebView2Runtime'
        if (-not (Test-WebView2)) { throw 'WebView2 설치를 확인할 수 없습니다. 설치 완료 후 다시 실행하세요.' }
    }
    Write-Host '[4/4] 시험 화면을 엽니다. 종료하기 또는 창의 X를 누르면 서버도 종료됩니다.'
    & $runtimePython (Join-Path $projectRoot 'desktop.py')
    if ($LASTEXITCODE -ne 0) { throw '시험 실행 중 오류가 발생했습니다.' }
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
