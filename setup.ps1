<#
.SYNOPSIS
    Tridatu-Shell — Automated Modern Terminal Setup for Windows
.DESCRIPTION
    Installs modern CLI tools (PowerShell 7, Starship, Zoxide, Eza, FZF, Delta, FD),
    configures optimized PowerShell 7 profile, sets Tridatu signature theme,
    disables terminal alert bell beeps, and optimizes Git diffs.
.USAGE
    irm https://raw.githubusercontent.com/Andndre/tridatu-shell/main/setup.ps1 | iex
#>

$ErrorActionPreference = 'Stop'

Write-Host "`n========================================================" -ForegroundColor Red
Write-Host "   TRIDATU-SHELL — MODERN TERMINAL AUTOMATION" -ForegroundColor White
Write-Host "========================================================`n" -ForegroundColor DarkGray

# 1. Package Installation via WinGet
Write-Host "[1/5] Memeriksa & Memasang Utilitas CLI Modern via WinGet..." -ForegroundColor Cyan
$packages = @(
    "Microsoft.PowerShell",
    "Starship.Starship",
    "ajeetdsouza.zoxide",
    "eza-community.eza",
    "junegunn.fzf",
    "dandavison.delta",
    "sharkdp.fd"
)

foreach ($pkg in $packages) {
    Write-Host "--> Memeriksa $pkg..." -NoNewline
    $installed = winget list --id $pkg --exact --accept-source-agreements 2>$null
    if ($LASTEXITCODE -eq 0 -and ($installed | Out-String) -match $pkg) {
        Write-Host " [Sudah Ada]" -ForegroundColor Green
    } else {
        Write-Host " [Menginstal...]" -ForegroundColor Yellow
        winget install --id $pkg --source winget --accept-source-agreements --accept-package-agreements --silent
    }
}

# 2. Git Config for Delta
Write-Host "`n[2/5] Mengonfigurasi Git Pager ke Delta..." -ForegroundColor Cyan
if (Get-Command git -ErrorAction SilentlyContinue) {
    git config --global core.pager "delta"
    git config --global interactive.diffFilter "delta --color-only"
    git config --global delta.navigate true
    git config --global delta.line-numbers true
    Write-Host "Git pager berhasil diarahkan ke Delta." -ForegroundColor Green
}

# 3. Menyiapkan Repositori Lokal (~/.tridatu-shell)
Write-Host "`n[3/6] Menyiapkan Direktori & Tema Tridatu-Shell (~/.tridatu-shell)..." -ForegroundColor Cyan
$installDir = Join-Path $HOME ".tridatu-shell"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (Test-Path (Join-Path $scriptDir "themes\tridatu.toml")) {
    # Dijalankan dari klon lokal
    if (!(Test-Path $installDir)) {
        Copy-Item $scriptDir $installDir -Recurse -Force | Out-Null
    }
} else {
    # Dijalankan via irm | iex
    if (Get-Command git -ErrorAction SilentlyContinue) {
        if (!(Test-Path $installDir)) {
            Write-Host "--> Mengkloning repositori ke $installDir..." -ForegroundColor DarkGray
            git clone --quiet https://github.com/Andndre/tridatu-shell.git $installDir
        } else {
            Write-Host "--> Memperbarui repositori di $installDir..." -ForegroundColor DarkGray
            git -C $installDir pull --quiet
        }
    }
}

# 4. Starship Config (Default: Tridatu Theme)
Write-Host "`n[4/6] Menyiapkan Konfigurasi Starship (~/.config/starship.toml)..." -ForegroundColor Cyan
$starshipConfigDir = Join-Path $HOME ".config"
if (!(Test-Path $starshipConfigDir)) {
    New-Item -ItemType Directory -Path $starshipConfigDir -Force | Out-Null
}

$starshipConfigPath = Join-Path $starshipConfigDir "starship.toml"
if (Test-Path $starshipConfigPath) {
    Copy-Item $starshipConfigPath "$starshipConfigPath.bak" -Force
}

$sourceTridatuTheme = Join-Path $installDir "themes\tridatu.toml"
if (Test-Path $sourceTridatuTheme) {
    Copy-Item $sourceTridatuTheme $starshipConfigPath -Force
    Write-Host "Tema signature Tridatu berhasil diterapkan." -ForegroundColor Green
} else {
    $remoteThemeUrl = "https://raw.githubusercontent.com/Andndre/tridatu-shell/main/themes/tridatu.toml"
    try {
        Invoke-RestMethod -Uri $remoteThemeUrl -OutFile $starshipConfigPath
        Write-Host "Tema signature Tridatu berhasil diunduh dan diterapkan." -ForegroundColor Green
    } catch {
        Write-Host "Catatan: Menggunakan konfigurasi default Starship." -ForegroundColor DarkGray
    }
}

# 5. PowerShell 7 Profile Configuration
Write-Host "`n[5/6] Menyiapkan Profil PowerShell 7 ($PROFILE)..." -ForegroundColor Cyan
$docsFolder = [Environment]::GetFolderPath('MyDocuments')
$ps7Dir = Join-Path $docsFolder "PowerShell"

if (!(Test-Path $ps7Dir)) {
    New-Item -ItemType Directory -Path $ps7Dir -Force | Out-Null
}

$ps7ProfilePath = Join-Path $ps7Dir "Microsoft.PowerShell_profile.ps1"
if (Test-Path $ps7ProfilePath) {
    Copy-Item $ps7ProfilePath "$ps7ProfilePath.bak" -Force
    Write-Host "Backup profil lama dibuat di $ps7ProfilePath.bak" -ForegroundColor DarkGray
}

$sourceProfile = Join-Path $installDir "configs\Microsoft.PowerShell_profile.ps1"
if (Test-Path $sourceProfile) {
    Copy-Item $sourceProfile $ps7ProfilePath -Force
    Write-Host "Profil PowerShell 7 berhasil dipasang." -ForegroundColor Green
} else {
    $remoteProfileUrl = "https://raw.githubusercontent.com/Andndre/tridatu-shell/main/configs/Microsoft.PowerShell_profile.ps1"
    try {
        Invoke-RestMethod -Uri $remoteProfileUrl -OutFile $ps7ProfilePath
        Write-Host "Profil PowerShell 7 berhasil diunduh dan dipasang." -ForegroundColor Green
    } catch {
        Write-Host "Gagal mengunduh profil remote: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 5. Windows Terminal Settings (Silence Bell & Default Profile)
Write-Host "`n[6/6] Mengatur Windows Terminal (Membisukan Bell & Menetapkan PS7 Default)..." -ForegroundColor Cyan
$wtSettingsPaths = @(
    "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json",
    "$env:LOCALAPPDATA\Microsoft\Windows Terminal\settings.json"
)

foreach ($wtPath in $wtSettingsPaths) {
    if (Test-Path $wtPath) {
        try {
            $json = Get-Content $wtPath -Raw -Encoding utf8 | ConvertFrom-Json
            if ($json.profiles.defaults) {
                $json.profiles.defaults | Add-Member -NotePropertyName "bellStyle" -NotePropertyValue "none" -Force
                $json.defaultProfile = "{574e775e-4f2a-5b96-ac1e-a2962a402336}"
                $json | ConvertTo-Json -Depth 32 | Set-Content -Path $wtPath -Encoding utf8
                Write-Host "Windows Terminal berhasil dikonfigurasi." -ForegroundColor Green
            }
        } catch {
            Write-Host "Peringatan: Windows Terminal settings tidak dapat diubah otomatis ($($_.Exception.Message))." -ForegroundColor DarkGray
        }
    }
}

Write-Host "`n========================================================" -ForegroundColor Red
Write-Host " INSTALASI TRIDATU-SHELL SELESAI!" -ForegroundColor Green
Write-Host " Langkah Terakhir untuk Pengguna:" -ForegroundColor Yellow
Write-Host " 1. Pastikan menginstal font Nerd Font (misal: CaskaydiaCove NF / JetBrainsMono NF)." -ForegroundColor White
Write-Host " 2. Di Windows Terminal: Settings -> Defaults -> Appearance -> Font Face -> pilih 'CaskaydiaCove NF'." -ForegroundColor White
Write-Host " 3. Buka tab baru di Windows Terminal untuk menikmati PowerShell 7." -ForegroundColor White
Write-Host " 4. Ketik 'tridatu-shell theme' kapan saja untuk mengganti tema!" -ForegroundColor Green
Write-Host "========================================================`n" -ForegroundColor Red
