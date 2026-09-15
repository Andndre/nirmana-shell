<#
.SYNOPSIS
    Nirmana-Shell Unified Theme Switcher
.DESCRIPTION
    Switches between custom Nirmana themes and official Starship presets dynamically
    with real-time interactive preview and rounded TUI borders.
.EXAMPLE
    .\switch-theme.ps1
    .\switch-theme.ps1 nirmana
    .\switch-theme.ps1 gruvbox-rainbow
#>

param (
    [string]$ThemeName
)

$scriptDir = if ($MyInvocation.MyCommand.Path) {
    Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
    Join-Path $HOME ".nirmana-shell"
}

$themesDir = Join-Path $scriptDir "themes"
$previewDir = Join-Path $scriptDir ".previews"
$targetConfig = Join-Path $HOME ".config\starship.toml"

# 1. Discover Custom Themes
$customThemes = @()
if (Test-Path $themesDir) {
    $customThemes = Get-ChildItem $themesDir -Filter "*.toml" | ForEach-Object { $_.BaseName }
}

# 2. Discover Official Starship Presets Dynamically (Excluding Custom Overrides)
$officialPresets = @()
if (Get-Command starship -ErrorAction SilentlyContinue) {
    try {
        $officialPresets = & starship preset --list 2>$null | Where-Object {
            -not [string]::IsNullOrWhiteSpace($_) -and ($customThemes -notcontains $_)
        }
    } catch {}
}

# 3. Ensure Preview Cache Exists
function Ensure-Previews {
    if (-not (Test-Path $previewDir) -or (Get-ChildItem $previewDir -Filter "*.txt").Count -eq 0) {
        if (!(Test-Path $previewDir)) { New-Item -ItemType Directory -Path $previewDir -Force | Out-Null }
        $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
        $esc = [char]27

        $customMeta = @{
            'nirmana'          = 'Clean contrast with geometric accents & cyan/purple highlights'
            'catppuccin-mocha' = 'Soothing pastel aesthetic based on Catppuccin Mocha'
            'tokyo-night'      = 'Cyberpunk dark theme inspired by Tokyo Night palette'
            'minimal-emerald'  = 'Distraction-free minimalist prompt with emerald green accents'
        }

        foreach ($c in $customThemes) {
            $desc = if ($customMeta.ContainsKey($c)) { $customMeta[$c] } else { 'Custom Starship theme' }
            $cfg = Join-Path $themesDir "$c.toml"
            $env:STARSHIP_CONFIG = $cfg
            $rendered = & starship prompt --path $scriptDir --status 0
            $content = @"

  $esc[1;36mTheme:$esc[0m      $esc[1;37m$c$esc[0m $esc[0;90m(Custom Theme)$esc[0m
  $esc[1;36mDetails:$esc[0m    $esc[0;37m$desc$esc[0m
  $esc[0;90m──────────────────────────────────────────────────────────────────────────────$esc[0m
  $esc[1;33mRendered Prompt:$esc[0m

  $rendered$esc[1;32mgit status$esc[0m

  $esc[0;90m──────────────────────────────────────────────────────────────────────────────$esc[0m
  $esc[0;90mControls: [Enter] Apply theme  |  [Esc] Cancel  |  [Arrows] Navigate$esc[0m
"@
            [System.IO.File]::WriteAllText((Join-Path $previewDir "$c.txt"), $content, $utf8NoBom)
        }

        $tempToml = Join-Path $env:TEMP "temp_preset.toml"
        foreach ($p in $officialPresets) {
            try {
                & starship preset $p > $tempToml
                $env:STARSHIP_CONFIG = $tempToml
                $rendered = & starship prompt --path $scriptDir --status 0
                $content = @"

  $esc[1;35mPreset:$esc[0m     $esc[1;37m$p$esc[0m $esc[0;90m(Official Starship Preset)$esc[0m
  $esc[1;35mSource:$esc[0m     $esc[0;37mhttps://starship.rs/presets/$esc[0m
  $esc[0;90m──────────────────────────────────────────────────────────────────────────────$esc[0m
  $esc[1;33mRendered Prompt:$esc[0m

  $rendered$esc[1;32mgit status$esc[0m

  $esc[0;90m──────────────────────────────────────────────────────────────────────────────$esc[0m
  $esc[0;90mControls: [Enter] Apply theme  |  [Esc] Cancel  |  [Arrows] Navigate$esc[0m
"@
                [System.IO.File]::WriteAllText((Join-Path $previewDir "$p.txt"), $content, $utf8NoBom)
            } catch {}
        }
        Remove-Item $tempToml -ErrorAction SilentlyContinue
    }
}

# 4. Interactive Selection via FZF if ThemeName is omitted
if (-not $ThemeName) {
    Ensure-Previews

    $menuItems = @()
    foreach ($c in $customThemes) {
        $menuItems += "[Custom]   $c"
    }
    foreach ($o in $officialPresets) {
        $menuItems += "[Official] $o"
    }

    if (Get-Command fzf -ErrorAction SilentlyContinue) {
        $previewScript = Join-Path $scriptDir "preview.cmd"
        $previewCmd = "`"$previewScript`" {}"
        $fzfArgs = @(
            "--prompt=  Select Theme ❯ ",
            "--pointer=◆ ",
            "--marker=✓ ",
            "--scrollbar=│",
            "--border=rounded",
            "--border-label= Nirmana Theme Switcher ",
            "--border-label-pos=3",
            "--preview-window=top:55%:border-rounded",
            "--preview-label= Real-Time Prompt Preview ",
            "--preview-label-pos=3",
            "--height=75%",
            "--reverse",
            "--preview=$previewCmd"
        )
        $selected = $menuItems | & fzf $fzfArgs
        if ($selected) {
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

# 5. Apply Theme or Preset
$targetConfigDir = Split-Path -Parent $targetConfig
if (!(Test-Path $targetConfigDir)) {
    New-Item -ItemType Directory -Path $targetConfigDir -Force | Out-Null
}

$isCustom = $customThemes -contains $cleanThemeName
$isOfficial = $officialPresets -contains $cleanThemeName

# 6. Windows Terminal Scheme Synchronization
$themeToWtScheme = @{
    'catppuccin-mocha' = 'Catppuccin Mocha'
    'tokyo-night'      = 'Tokyo Night'
    'nirmana'          = 'Nirmana'
    'minimal-emerald'  = 'Catppuccin Mocha'
}

$wtCandidatePaths = @(
    "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json",
    "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json",
    "$env:LOCALAPPDATA\Microsoft\Windows Terminal\settings.json"
)

$syncedWtScheme = $null
if ($themeToWtScheme.ContainsKey($cleanThemeName)) {
    $targetWtScheme = $themeToWtScheme[$cleanThemeName]
    foreach ($wtPath in $wtCandidatePaths) {
        if (Test-Path $wtPath) {
            try {
                $raw = Get-Content $wtPath -Raw -Encoding utf8
                if ($raw -match '"colorScheme"\s*:\s*"[^"]*"') {
                    $updated = $raw -replace '("colorScheme"\s*:\s*)"[^"]*"', "`$1`"$targetWtScheme`""
                    Set-Content -Path $wtPath -Value $updated -Encoding utf8
                    $syncedWtScheme = $targetWtScheme
                    break
                }
            } catch {}
        }
    }
}

if ($isCustom) {
    $sourceTheme = Join-Path $themesDir "$cleanThemeName.toml"
    Copy-Item $sourceTheme $targetConfig -Force
    Write-Host ""
    Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Green
    Write-Host "│  Custom Theme Applied: $($cleanThemeName.PadRight(44))│" -ForegroundColor Green
    if ($syncedWtScheme) {
        Write-Host "├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkGray
        Write-Host "│  Terminal Scheme: $($syncedWtScheme.PadRight(47))│" -ForegroundColor Cyan
    }
    Write-Host "├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkGray
    Write-Host "│  Saved to: ~/.config/starship.toml                          │" -ForegroundColor DarkGray
    Write-Host "│  Reload session: nirmana reload                             │" -ForegroundColor DarkGray
    Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Green
    Write-Host ""
} elseif ($isOfficial) {
    & starship preset $cleanThemeName -o $targetConfig -f
    
    # Ensure scan_timeout = 30 and command_timeout = 1000 are present for Windows NTFS performance
    $content = Get-Content $targetConfig -Raw -Encoding utf8
    if ($content -notmatch 'scan_timeout\s*=') {
        $content = "scan_timeout = 30`n" + $content
    }
    if ($content -notmatch 'command_timeout\s*=') {
        $content = "command_timeout = 1000`n" + $content
    }
    # Normalize incompatible Nerd Font v3-only codepoints to universal Nerd Font glyphs
    $content = $content -replace "󰏗", ""
    $content = $content -replace "", ""
    Set-Content -Path $targetConfig -Value $content -Encoding utf8
    
    Write-Host ""
    Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Green
    Write-Host "│  Official Preset Applied: $($cleanThemeName.PadRight(42))│" -ForegroundColor Green
    if ($syncedWtScheme) {
        Write-Host "├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkGray
        Write-Host "│  Terminal Scheme: $($syncedWtScheme.PadRight(47))│" -ForegroundColor Cyan
    }
    Write-Host "├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkGray
    Write-Host "│  Source: https://starship.rs/presets/                       │" -ForegroundColor DarkGray
    Write-Host "│  Saved to: ~/.config/starship.toml                          │" -ForegroundColor DarkGray
    Write-Host "│  Reload session: nirmana reload                             │" -ForegroundColor DarkGray
    Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Error "Theme '$cleanThemeName' not found in custom themes ($($customThemes -join ', ')) or official presets ($($officialPresets -join ', '))"
    exit 1
}
