<#
.SYNOPSIS
    Nirmana-Shell Unified Theme Switcher
.DESCRIPTION
    Switches between custom Nirmana themes and official Starship presets dynamically.
.EXAMPLE
    .\switch-theme.ps1
    .\switch-theme.ps1 nirmana
    .\switch-theme.ps1 gruvbox-rainbow
    .\switch-theme.ps1 pastel-powerline
    .\switch-theme.ps1 catppuccin-mocha
#>

param (
    [string]$ThemeName
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$themesDir = Join-Path $scriptDir "themes"
$targetConfig = Join-Path $HOME ".config\starship.toml"

# 1. Discover Custom Themes
$customThemes = @()
if (Test-Path $themesDir) {
    $customThemes = Get-ChildItem $themesDir -Filter "*.toml" | ForEach-Object { $_.BaseName }
}

# 2. Discover Official Starship Presets Dynamically
$officialPresets = @()
if (Get-Command starship -ErrorAction SilentlyContinue) {
    try {
        $officialPresets = & starship preset --list 2>$null
    } catch {}
}

# 3. Interactive Selection via FZF if ThemeName is omitted
if (-not $ThemeName) {
    $menuItems = @()
    foreach ($c in $customThemes) {
        $menuItems += "[Custom]   $c"
    }
    foreach ($o in $officialPresets) {
        $menuItems += "[Official] $o"
    }

    if (Get-Command fzf -ErrorAction SilentlyContinue) {
        $selected = $menuItems | fzf --prompt="Select Theme / Preset> " --height=40% --reverse --border
        if ($selected) {
            # Extract clean theme name
            $ThemeName = ($selected -replace '^\[(Custom|Official)\]\s+', '').Trim()
        }
    } else {
        Write-Host "`nAvailable Themes & Presets:" -ForegroundColor Cyan
        for ($i = 0; $i -lt $menuItems.Count; $i++) {
            Write-Host "[$($i+1)] $($menuItems[$i])"
        }
        $choice = Read-Host "`nEnter number (1-$($menuItems.Count))"
        if ($choice -match '^\d+$' -and [int]$choice -le $menuItems.Count -and [int]$choice -gt 0) {
            $selected = $menuItems[[int]$choice - 1]
            $ThemeName = ($selected -replace '^\[(Custom|Official)\]\s+', '').Trim()
        }
    }
}

if (-not $ThemeName) {
    Write-Host "Theme selection cancelled." -ForegroundColor Yellow
    exit 0
}

# Clean input if user passed bracketed label
$cleanThemeName = ($ThemeName -replace '^\[(Custom|Official)\]\s+', '').Trim()

# 4. Apply Theme or Preset
$targetConfigDir = Split-Path -Parent $targetConfig
if (!(Test-Path $targetConfigDir)) {
    New-Item -ItemType Directory -Path $targetConfigDir -Force | Out-Null
}

$isCustom = $customThemes -contains $cleanThemeName
$isOfficial = $officialPresets -contains $cleanThemeName

if ($isCustom) {
    $sourceTheme = Join-Path $themesDir "$cleanThemeName.toml"
    Copy-Item $sourceTheme $targetConfig -Force
    Write-Host "Successfully applied custom theme: $cleanThemeName" -ForegroundColor Green
    Write-Host "Saved to $targetConfig (Open a new tab to see visual changes)." -ForegroundColor Cyan
} elseif ($isOfficial) {
    & starship preset $cleanThemeName -o $targetConfig -f
    
    # Ensure scan_timeout = 30 is present for Windows NTFS performance
    $content = Get-Content $targetConfig -Raw -Encoding utf8
    if ($content -notmatch 'scan_timeout\s*=') {
        $content = "scan_timeout = 30`n" + $content
        Set-Content -Path $targetConfig -Value $content -Encoding utf8
    }
    
    Write-Host "Successfully applied official Starship preset: $cleanThemeName" -ForegroundColor Green
    Write-Host "Source: Official Starship presets (https://starship.rs/presets/)" -ForegroundColor DarkGray
    Write-Host "Saved to $targetConfig (Open a new tab to see visual changes)." -ForegroundColor Cyan
} else {
    Write-Error "Theme '$cleanThemeName' not found in custom themes ($($customThemes -join ', ')) or official presets ($($officialPresets -join ', '))"
    exit 1
}
