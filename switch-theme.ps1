<#
.SYNOPSIS
    Nirmana-Shell Theme Switcher
.DESCRIPTION
    Instantly switches the Starship visual theme.
.EXAMPLE
    .\switch-theme.ps1
    .\switch-theme.ps1 nirmana
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
    Write-Error "Themes directory not found at $themesDir"
    exit 1
}

$availableThemes = Get-ChildItem $themesDir -Filter "*.toml" | ForEach-Object { $_.BaseName }

if (-not $ThemeName) {
    if (Get-Command fzf -ErrorAction SilentlyContinue) {
        $ThemeName = $availableThemes | fzf --prompt="Select Nirmana-Shell Theme> " --height=30% --reverse --border
    } else {
        Write-Host "Available themes:" -ForegroundColor Cyan
        for ($i = 0; $i -lt $availableThemes.Count; $i++) {
            Write-Host "[$($i+1)] $($availableThemes[$i])"
        }
        $choice = Read-Host "Enter theme number (1-$($availableThemes.Count))"
        if ($choice -match '^\d+$' -and [int]$choice -le $availableThemes.Count -and [int]$choice -gt 0) {
            $ThemeName = $availableThemes[[int]$choice - 1]
        }
    }
}

if (-not $ThemeName) {
    Write-Host "Theme selection cancelled." -ForegroundColor Yellow
    exit 0
}

$sourceTheme = Join-Path $themesDir "$ThemeName.toml"
if (!(Test-Path $sourceTheme)) {
    Write-Error "Theme '$ThemeName' not found! Available options: $($availableThemes -join ', ')"
    exit 1
}

Copy-Item $sourceTheme $targetConfig -Force
Write-Host "Successfully applied theme: $ThemeName" -ForegroundColor Green
Write-Host "Theme saved to $targetConfig (Open a new tab to see visual changes)." -ForegroundColor Cyan
