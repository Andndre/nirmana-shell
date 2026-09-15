<#
.SYNOPSIS
    Tridatu-Shell Theme Switcher
.DESCRIPTION
    Mengganti tema visual Starship secara instan.
.EXAMPLE
    .\switch-theme.ps1
    .\switch-theme.ps1 tridatu
    .\switch-theme.ps1 tokyo-night
    .\switch-theme.ps1 catppuccin-mocha
    .\switch-theme.ps1 minimal-emerald
#>

param (
    [string]$ThemeName
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$themesDir = Join-Path $scriptDir "themes"
$targetConfig = Join-Path $HOME ".config\starship.toml"

if (!(Test-Path $themesDir)) {
    Write-Error "Folder themes tidak ditemukan di $themesDir"
    exit 1
}

$availableThemes = Get-ChildItem $themesDir -Filter "*.toml" | ForEach-Object { $_.BaseName }

if (-not $ThemeName) {
    if (Get-Command fzf -ErrorAction SilentlyContinue) {
        $ThemeName = $availableThemes | fzf --prompt="Pilih Tema Tridatu-Shell> " --height=30% --reverse --border
    } else {
        Write-Host "Tema yang tersedia:" -ForegroundColor Cyan
        for ($i = 0; $i -lt $availableThemes.Count; $i++) {
            Write-Host "[$($i+1)] $($availableThemes[$i])"
        }
        $pilihan = Read-Host "Masukkan nomor tema (1-$($availableThemes.Count))"
        if ($pilihan -match '^\d+$' -and [int]$pilihan -le $availableThemes.Count -and [int]$pilihan -gt 0) {
            $ThemeName = $availableThemes[[int]$pilihan - 1]
        }
    }
}

if (-not $ThemeName) {
    Write-Host "Pemilihan tema dibatalkan." -ForegroundColor Yellow
    exit 0
}

$sourceTheme = Join-Path $themesDir "$ThemeName.toml"
if (!(Test-Path $sourceTheme)) {
    Write-Error "Tema '$ThemeName' tidak ditemukan! Pilihan: $($availableThemes -join ', ')"
    exit 1
}

Copy-Item $sourceTheme $targetConfig -Force
Write-Host "Berhasil menerapkan tema: $ThemeName" -ForegroundColor Green
Write-Host "Tema tersimpan di $targetConfig (Buka tab baru untuk melihat perubahan visual)." -ForegroundColor Cyan
