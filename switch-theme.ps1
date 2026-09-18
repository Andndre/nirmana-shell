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
    [string]$ThemeName,
    [switch]$UpdatePreviews
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
    $customThemes = Get-ChildItem $themesDir -File -Filter "*.toml" | ForEach-Object { $_.BaseName }
}

# 2. Discover Starship Presets Dynamically (Excluding Custom Overrides)
$starshipPresets = @()
if (Get-Command starship -ErrorAction SilentlyContinue) {
    try {
        $starshipPresets = & starship preset --list 2>$null | Where-Object {
            -not [string]::IsNullOrWhiteSpace($_) -and ($customThemes -notcontains $_)
        }
    } catch {}
}

# 3. Ensure Preview Cache Exists
function Ensure-Previews ([switch]$Force) {
    $previewCount = if (Test-Path $previewDir) { (Get-ChildItem $previewDir -Filter "*.txt").Count } else { 0 }
    $expectedCount = $customThemes.Count + $starshipPresets.Count
    if ($Force -or -not (Test-Path $previewDir) -or $previewCount -lt $expectedCount) {
        if (!(Test-Path $previewDir)) { New-Item -ItemType Directory -Path $previewDir -Force | Out-Null }
        $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
        $esc = [char]27
        $origConfig = $env:STARSHIP_CONFIG
        $origAdmin = $env:STARSHIP_IS_ADMIN
        $env:STARSHIP_IS_ADMIN = "1"

        $mockBase = Join-Path $env:TEMP "nirmana-preview-mock"
        $mockDir = Join-Path $mockBase "nirmana-shell"
        $previewTarget = $scriptDir
        try {
            if (Test-Path $mockBase) { Remove-Item -Recurse -Force $mockBase -ErrorAction SilentlyContinue }
            New-Item -ItemType Directory -Path $mockDir -Force | Out-Null
            Set-Content (Join-Path $mockDir "package.json") '{"name": "nirmana-shell", "version": "1.0.0"}' -Encoding utf8
            Set-Content (Join-Path $mockDir "main.c") "int main() {}" -Encoding utf8
            Set-Content (Join-Path $mockDir "app.py") "print('hello')" -Encoding utf8
            if (Get-Command git -ErrorAction SilentlyContinue) {
                & git -C $mockDir init -b main --quiet 2>$null
                & git -C $mockDir config user.name "Nirmana" 2>$null
                & git -C $mockDir config user.email "nirmana@shell.local" 2>$null
                & git -C $mockDir add -A 2>$null
                & git -C $mockDir commit -m "init" --quiet 2>$null
                Add-Content (Join-Path $mockDir "main.c") "`n// change" -Encoding utf8
            }
            $previewTarget = $mockDir
        } catch {}

        try {
            $customMeta = @{
                'nirmana'               = 'Signature theme with geometric accents & cyan/purple highlights'
                'catppuccin-mocha'      = 'Soothing pastel aesthetic based on Catppuccin Mocha'
                'tokyo-night'           = 'Cyberpunk dark theme inspired by Tokyo Night palette'
                'minimal-emerald'       = 'Distraction-free minimalist prompt with emerald green accents'
                'jetpack'               = 'Futuristic geometric prompt with unicode accents (Windows-adapted)'
                'bubbles'               = 'Rounded capsule segments with deep indigo & vibrant accents (Bubble style)'
                'jandedobbeleer'        = 'Signature powerline chevron theme with pink & yellow accents'
                'atomic'                = 'Two-line rounded pill segments with warm orange/yellow highlights'
                'agnoster'              = 'Classic legendary powerline chevron arrow theme'
                'powerlevel10k_rainbow' = 'Iconic multi-color powerline rainbow theme (Powerlevel10k style)'
                'dracula'               = 'Official Dracula gothic pastel palette with rounded capsules'
                'paradox'               = 'Vibrant classic chevron theme with sky blue directory'
                'half-life'             = 'Cyberpunk lambda prompt with electric green & orange accents'
                'robbyrussell'          = 'Legendary minimal arrow prompt with colored git & runtime status'
                'spaceship'             = 'Cosmic developer prompt with rocket execution symbol'
                'clean-detailed'        = 'Modern two-line prompt with right-aligned runtime & duration'
                'takuya'                = 'Craftzdog signature prompt with right-aligned runtime & clock'
                '1_shell'               = 'Clean pastel two-line prompt with system info ported from Oh My Posh'
            }

            foreach ($c in $customThemes) {
                $cfg = Join-Path $themesDir "$c.toml"
                $cfgRaw = Get-Content $cfg -Raw -ErrorAction SilentlyContinue
                $isOmp = $cfgRaw -match 'Ported from Oh My Posh'
                $catLabel = if ($isOmp) { '[Oh-My-Posh]' } else { '[Custom]' }
                $catColor = if ($isOmp) { '35m' } else { '36m' }
                $desc = if ($customMeta.ContainsKey($c)) {
                    $customMeta[$c]
                } elseif ($isOmp) {
                    'Community theme ported from Oh My Posh'
                } else {
                    'Custom Starship theme'
                }
                $env:STARSHIP_CONFIG = $cfg
                $lines = & starship prompt --path $previewTarget --status 0 --cmd-duration 2500 --terminal-width 78
                while ($lines.Count -gt 0 -and [string]::IsNullOrWhiteSpace($lines[0])) {
                    $lines = $lines[1..($lines.Count - 1)]
                }
                $indented = ($lines | ForEach-Object { "  $_" }) -join "`n"
                $content = @"

  $esc[1;$catColor Category:$esc[0m   $esc[1;37m$catLabel$esc[0m
  $esc[1;36mTheme:$esc[0m      $esc[1;37m$c$esc[0m
  $esc[1;36mDetails:$esc[0m    $esc[0;37m$desc$esc[0m
  $esc[0;90m──────────────────────────────────────────────────────────────────────────────$esc[0m
  $esc[1;33mRendered Prompt:$esc[0m

$indented$esc[1;32mgit status$esc[0m

  $esc[0;90m──────────────────────────────────────────────────────────────────────────────$esc[0m
  $esc[0;90mControls: [Enter] Apply theme  |  [Esc] Cancel  |  [Arrows] Navigate$esc[0m
"@
                [System.IO.File]::WriteAllText((Join-Path $previewDir "$c.txt"), $content, $utf8NoBom)
            }

            $tempToml = Join-Path $env:TEMP "temp_preset.toml"
            foreach ($p in $starshipPresets) {
                try {
                    & starship preset $p > $tempToml
                    $env:STARSHIP_CONFIG = $tempToml
                    $lines = & starship prompt --path $previewTarget --status 0 --cmd-duration 2500 --terminal-width 78
                    while ($lines.Count -gt 0 -and [string]::IsNullOrWhiteSpace($lines[0])) {
                        $lines = $lines[1..($lines.Count - 1)]
                    }
                    $indented = ($lines | ForEach-Object { "  $_" }) -join "`n"
                    $content = @"

  $esc[1;34mCategory:$esc[0m   $esc[1;37m[Starship]$esc[0m
  $esc[1;34mPreset:$esc[0m     $esc[1;37m$p$esc[0m $esc[0;90m(Official Starship Preset)$esc[0m
  $esc[1;34mSource:$esc[0m     $esc[0;37mhttps://starship.rs/presets/$esc[0m
  $esc[0;90m──────────────────────────────────────────────────────────────────────────────$esc[0m
  $esc[1;33mRendered Prompt:$esc[0m

$indented$esc[1;32mgit status$esc[0m

  $esc[0;90m──────────────────────────────────────────────────────────────────────────────$esc[0m
  $esc[0;90mControls: [Enter] Apply theme  |  [Esc] Cancel  |  [Arrows] Navigate$esc[0m
"@
                    [System.IO.File]::WriteAllText((Join-Path $previewDir "$p.txt"), $content, $utf8NoBom)
                } catch {}
            }
            Remove-Item $tempToml -ErrorAction SilentlyContinue
        } finally {
            if ($mockBase -and (Test-Path $mockBase)) {
                Remove-Item -Recurse -Force $mockBase -ErrorAction SilentlyContinue
            }
            if ($origConfig -and (Test-Path $origConfig)) {
                $env:STARSHIP_CONFIG = $origConfig
            } else {
                Remove-Item Env:\STARSHIP_CONFIG -ErrorAction SilentlyContinue
            }
            if ($null -ne $origAdmin) {
                $env:STARSHIP_IS_ADMIN = $origAdmin
            } else {
                Remove-Item Env:\STARSHIP_IS_ADMIN -ErrorAction SilentlyContinue
            }
        }
    }
}

if ($UpdatePreviews) {
    Ensure-Previews -Force
    $count = (Get-ChildItem $previewDir -Filter "*.txt").Count
    Write-Host "Preview cache generated successfully: $count previews in $previewDir" -ForegroundColor Green
    exit 0
}

# 4. Interactive Selection via FZF if ThemeName is omitted
if (-not $ThemeName) {
    Ensure-Previews

    $menuItems = @()
    foreach ($c in $customThemes) {
        $cfg = Join-Path $themesDir "$c.toml"
        $cfgRaw = Get-Content $cfg -Raw -ErrorAction SilentlyContinue
        if ($cfgRaw -match 'Ported from Oh My Posh') {
            $menuItems += "[Oh-My-Posh] $c"
        } else {
            $menuItems += "[Custom]     $c"
        }
    }
    foreach ($s in $starshipPresets) {
        $menuItems += "[Starship]   $s"
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
            $ThemeName = ($selected.Trim([char]0xFEFF) -replace '^[\uFEFF\s]*\[(Custom|Starship|Official|Oh-My-Posh)\]\s+', '').Trim()
        }
    } else {
        Write-Host "`nAvailable Themes & Presets:" -ForegroundColor Cyan
        for ($i = 0; $i -lt $menuItems.Count; $i++) {
            Write-Host "[$($i+1)] $($menuItems[$i])"
        }
        $choice = Read-Host "`nEnter number (1-$($menuItems.Count))"
        if ($choice -match '^\d+$' -and [int]$choice -le $menuItems.Count -and [int]$choice -gt 0) {
            $selected = $menuItems[[int]$choice - 1]
            $ThemeName = ($selected.Trim([char]0xFEFF) -replace '^[\uFEFF\s]*\[(Custom|Starship|Official|Oh-My-Posh)\]\s+', '').Trim()
        }
    }
}

if (-not $ThemeName) {
    Write-Host "Theme selection cancelled." -ForegroundColor Yellow
    exit 0
}

# Clean input if user passed bracketed label
$cleanThemeName = ($ThemeName.Trim([char]0xFEFF) -replace '^[\uFEFF\s]*\[(Custom|Starship|Official|Oh-My-Posh)\]\s+', '').Trim()

# 6. Apply Theme or Preset
$targetConfigDir = Split-Path -Parent $targetConfig
if (!(Test-Path $targetConfigDir)) {
    New-Item -ItemType Directory -Path $targetConfigDir -Force | Out-Null
}

$isCustom = $customThemes -contains $cleanThemeName
$isStarship = $starshipPresets -contains $cleanThemeName

# 7. Windows Terminal Scheme Synchronization
$themeToWtScheme = @{
    'catppuccin-mocha'      = 'Catppuccin Mocha'
    'tokyo-night'           = 'Tokyo Night'
    'nirmana'               = 'Nirmana'
    'minimal-emerald'       = 'Catppuccin Mocha'
    'jetpack'               = 'Tokyo Night'
    'bubbles'               = 'Tokyo Night'
    'jandedobbeleer'        = 'Catppuccin Mocha'
    'atomic'                = 'Catppuccin Mocha'
    'agnoster'              = 'Tokyo Night'
    'powerlevel10k_rainbow' = 'Catppuccin Mocha'
    'dracula'               = 'Dracula'
    'paradox'               = 'Catppuccin Mocha'
    'half-life'             = 'Tokyo Night'
    'robbyrussell'          = 'Catppuccin Mocha'
    'spaceship'             = 'Tokyo Night'
    'clean-detailed'        = 'Nirmana'
    'takuya'                = 'Tokyo Night'
    'night-owl'             = 'Night Owl'
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
                $modified = $false
                try {
                    $jsonObj = $raw | ConvertFrom-Json
                    if ($jsonObj.profiles.defaults) {
                        $jsonObj.profiles.defaults.colorScheme = $targetWtScheme
                        $raw = $jsonObj | ConvertTo-Json -Depth 10
                        $modified = $true
                    }
                } catch {
                    if ($raw -match '("defaults"\s*:\s*\{[\s\S]*?\n\s*\})(?=\s*,\s*("list"|\}))') {
                        $defaultsBlock = $Matches[1]
                        $updatedDefaults = $defaultsBlock
                        if ($updatedDefaults -match '("colorScheme"\s*:\s*)"[^"]*"') {
                            $updatedDefaults = [regex]::new('("colorScheme"\s*:\s*)"[^"]*"').Replace($updatedDefaults, "`$1`"$targetWtScheme`"", 1)
                        } else {
                            $updatedDefaults = $updatedDefaults -replace '("defaults"\s*:\s*\{)', "`$1`n      `"colorScheme`": `"$targetWtScheme`","
                        }
                        if ($updatedDefaults -ne $defaultsBlock) {
                            $raw = $raw.Replace($defaultsBlock, $updatedDefaults)
                            $modified = $true
                        }
                    }
                }
                if ($modified) {
                    Set-Content -Path $wtPath -Value $raw -Encoding utf8
                    $syncedWtScheme = $targetWtScheme
                }
            } catch {}
        }
    }
}

# Persist active theme in Nirmana settings (~/.config/nirmana/settings.json)
try {
    $nirmanaConfigDir = Join-Path $HOME ".config\nirmana"
    if (!(Test-Path $nirmanaConfigDir)) {
        New-Item -ItemType Directory -Path $nirmanaConfigDir -Force | Out-Null
    }
    $nirmanaConfigFile = Join-Path $nirmanaConfigDir "settings.json"
    $cfg = if (Test-Path $nirmanaConfigFile) {
        try { Get-Content $nirmanaConfigFile -Raw -Encoding utf8 | ConvertFrom-Json } catch { [pscustomobject]@{} }
    } else {
        [pscustomobject]@{}
    }
    if ($cfg.PSObject.Properties['theme']) {
        $cfg.theme = $cleanThemeName
    } else {
        $cfg | Add-Member -NotePropertyName 'theme' -NotePropertyValue $cleanThemeName -Force
    }
    $json = $cfg | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText($nirmanaConfigFile, $json, [System.Text.UTF8Encoding]::new($false))
} catch {}

if ($isCustom) {
    $sourceTheme = Join-Path $themesDir "$cleanThemeName.toml"
    Copy-Item $sourceTheme $targetConfig -Force
    $env:STARSHIP_CONFIG = $targetConfig
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
} elseif ($isStarship) {
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
    $env:STARSHIP_CONFIG = $targetConfig
    
    Write-Host ""
    Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Blue
    Write-Host "│  Starship Preset Applied: $($cleanThemeName.PadRight(41))│" -ForegroundColor Blue
    if ($syncedWtScheme) {
        Write-Host "├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkGray
        Write-Host "│  Terminal Scheme: $($syncedWtScheme.PadRight(47))│" -ForegroundColor Cyan
    }
    Write-Host "├─────────────────────────────────────────────────────────────┤" -ForegroundColor DarkGray
    Write-Host "│  Source: https://starship.rs/presets/                       │" -ForegroundColor DarkGray
    Write-Host "│  Saved to: ~/.config/starship.toml                          │" -ForegroundColor DarkGray
    Write-Host "│  Reload session: nirmana reload                             │" -ForegroundColor DarkGray
    Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Blue
    Write-Host ""
} else {
    Write-Error "Theme '$cleanThemeName' not found in [Custom] ($($customThemes -join ', ')) or [Starship] presets."
    exit 1
}
