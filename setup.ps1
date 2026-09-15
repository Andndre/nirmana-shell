# =====================================================================
# Nirmana-Shell: Automated Modern Terminal Setup for Windows
# Usage: irm https://raw.githubusercontent.com/Andndre/nirmana-shell/main/setup.ps1 | iex
# =====================================================================

$ErrorActionPreference = 'Stop'

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$setupScriptDir = if ($PSScriptRoot) {
    $PSScriptRoot
} elseif ($MyInvocation.MyCommand.Path) {
    Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
    $null
}
$versionFile = if ($setupScriptDir) { Join-Path $setupScriptDir "VERSION" } else { $null }
$nirmanaVer = if ($versionFile -and (Test-Path $versionFile)) { (Get-Content $versionFile -Raw).Trim() } else { "1.0.7" }
$isLegacyPS = $PSVersionTable.PSVersion.Major -lt 7

Write-Host ""
Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
Write-Host "│      NIRMANA-SHELL: MODERN TERMINAL AUTOMATION (v$nirmanaVer)     │" -ForegroundColor White
Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
if ($isLegacyPS) {
    Write-Host "Note: Running from Windows PowerShell $($PSVersionTable.PSVersion.Major).$($PSVersionTable.PSVersion.Minor). PowerShell 7 will be installed as default." -ForegroundColor DarkYellow
}
Write-Host ""

# 1. Package Installation via WinGet
Write-Host "[1/6] Checking & Installing Modern CLI Tools via WinGet..." -ForegroundColor Cyan
$packages = @(
    @{ Id = "Microsoft.PowerShell"; Source = "winget" },
    @{ Id = "Git.Git"; Source = "winget" },
    @{ Id = "Starship.Starship"; Source = "winget" },
    @{ Id = "ajeetdsouza.zoxide"; Source = "winget" },
    @{ Id = "eza-community.eza"; Source = "winget" },
    @{ Id = "junegunn.fzf"; Source = "winget" },
    @{ Id = "dandavison.delta"; Source = "winget" },
    @{ Id = "sharkdp.fd"; Source = "winget" },
    @{ Id = "BurntSushi.ripgrep.MSVC"; Source = "winget" },
    @{ Id = "ryanoasis.CaskaydiaCove"; Source = "winget-font" }
)

function Test-NerdFontInstalled {
    $fontDirs = @(
        "$env:LOCALAPPDATA\Microsoft\Windows\Fonts",
        "$env:WINDIR\Fonts"
    )
    foreach ($d in $fontDirs) {
        if (Test-Path $d) {
            $found = Get-ChildItem -Path $d -Filter "*Caskaydia*Nerd*.ttf" -ErrorAction SilentlyContinue
            if (-not $found) {
                $found = Get-ChildItem -Path $d -Filter "*Caskaydia*NF*.ttf" -ErrorAction SilentlyContinue
            }
            if ($found) { return $true }
        }
    }
    return $false
}

foreach ($item in $packages) {
    $pkg = $item.Id
    $src = $item.Source
    Write-Host "--> Checking $pkg..." -NoNewline
    
    $isInstalled = $false
    if ($pkg -eq "ryanoasis.CaskaydiaCove" -and (Test-NerdFontInstalled)) {
        $isInstalled = $true
    } else {
        $installed = winget list --id $pkg --exact --accept-source-agreements 2>$null
        if ($LASTEXITCODE -eq 0 -and ($installed | Out-String) -match [regex]::Escape($pkg)) {
            $isInstalled = $true
        }
    }

    if ($isInstalled) {
        Write-Host " [Installed]" -ForegroundColor Green
    } else {
        Write-Host " [Installing...]" -ForegroundColor Yellow
        winget install --id $pkg --source $src --accept-source-agreements --accept-package-agreements --silent
    }
}

# 2. Git Config for Delta
Write-Host "`n[2/6] Configuring Git Pager to Delta..." -ForegroundColor Cyan
if (Get-Command git -ErrorAction SilentlyContinue) {
    git config --global core.pager "delta"
    git config --global interactive.diffFilter "delta --color-only"
    git config --global delta.navigate true
    git config --global delta.line-numbers true
    Write-Host "Git pager successfully routed to Delta." -ForegroundColor Green
}

# 3. Setup Local Repository Directory (~/.nirmana-shell)
Write-Host "`n[3/6] Setting Up Nirmana-Shell Directory (~/.nirmana-shell)..." -ForegroundColor Cyan
$installDir = Join-Path $HOME ".nirmana-shell"
$hasLocalSource = $MyInvocation.MyCommand.Path -and (Test-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "themes\nirmana.toml"))

if ($hasLocalSource) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $isSelfDir = [string]::Equals(
        [System.IO.Path]::GetFullPath($scriptDir).TrimEnd('\', '/'),
        [System.IO.Path]::GetFullPath($installDir).TrimEnd('\', '/'),
        [System.StringComparison]::OrdinalIgnoreCase
    )

    if (-not $isSelfDir) {
        Write-Host "--> Copying files to $installDir..." -ForegroundColor DarkGray
        if (!(Test-Path $installDir)) {
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
        }
        Get-ChildItem -Path $scriptDir -Exclude ".git" | Copy-Item -Destination $installDir -Recurse -Force
    } else {
        Write-Host "--> Already running from install directory ($installDir)." -ForegroundColor DarkGray
    }
} else {
    # Running remotely via irm | iex
    if (Get-Command git -ErrorAction SilentlyContinue) {
        if (!(Test-Path $installDir)) {
            Write-Host "--> Cloning repository to $installDir..." -ForegroundColor DarkGray
            git clone --quiet https://github.com/Andndre/nirmana-shell.git $installDir
        } else {
            Write-Host "--> Updating repository in $installDir..." -ForegroundColor DarkGray
            git -C $installDir fetch --quiet origin main 2>$null
            git -C $installDir reset --hard origin/main 2>$null
        }
    } else {
        # Fallback: Download archive if git is not yet available in current session PATH
        Write-Host "--> Downloading Nirmana-Shell package..." -ForegroundColor DarkGray
        $zipUrl = "https://github.com/Andndre/nirmana-shell/archive/refs/heads/main.zip"
        $tempZip = Join-Path $env:TEMP "nirmana-shell.zip"
        $tempExtract = Join-Path $env:TEMP "nirmana-shell-extract"
        Invoke-RestMethod -Uri $zipUrl -OutFile $tempZip
        Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
        if (!(Test-Path $installDir)) {
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
        }
        Copy-Item (Join-Path $tempExtract "nirmana-shell-main\*") $installDir -Recurse -Force
        Remove-Item $tempZip, $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Pre-seed initial directories into Zoxide if database is brand new
    if (Get-Command zoxide -ErrorAction SilentlyContinue) {
        try {
            $existing = & zoxide query -l 2>$null
            if (-not $existing) {
                & zoxide add $HOME 2>$null
                & zoxide add (Join-Path $HOME "Downloads") 2>$null
                & zoxide add $installDir 2>$null
            }
        } catch {}
    }
}

# 4. Starship Config (Theme Persistence & Safety)
Write-Host "`n[4/6] Setting Up Starship Configuration (~/.config/starship.toml)..." -ForegroundColor Cyan
$starshipConfigDir = Join-Path $HOME ".config"
if (!(Test-Path $starshipConfigDir)) {
    New-Item -ItemType Directory -Path $starshipConfigDir -Force | Out-Null
}

$starshipConfigPath = Join-Path $starshipConfigDir "starship.toml"
$nirmanaConfigDir = Join-Path $HOME ".config\nirmana"
$nirmanaConfigFile = Join-Path $nirmanaConfigDir "settings.json"

$savedTheme = $null
if (Test-Path $nirmanaConfigFile) {
    try {
        $savedSettings = Get-Content $nirmanaConfigFile -Raw -Encoding utf8 | ConvertFrom-Json
        if ($savedSettings.theme) { $savedTheme = $savedSettings.theme }
    } catch {}
}

if ($savedTheme) {
    # Active theme recorded in settings.json - preserve and update that specific theme
    $customThemePath = Join-Path $installDir "themes\$savedTheme.toml"
    if (Test-Path $customThemePath) {
        Copy-Item $customThemePath $starshipConfigPath -Force
        Write-Host "Active theme '$savedTheme' preserved and updated from repository." -ForegroundColor Green
    } elseif (Get-Command starship -ErrorAction SilentlyContinue) {
        try {
            & starship preset $savedTheme -o $starshipConfigPath -f 2>$null
            Write-Host "Active Starship preset '$savedTheme' preserved." -ForegroundColor Green
        } catch {
            Write-Host "Existing configuration preserved for '$savedTheme'." -ForegroundColor Green
        }
    } else {
        Write-Host "Existing Starship configuration preserved for '$savedTheme'." -ForegroundColor Green
    }
} elseif (Test-Path $starshipConfigPath) {
    # Existing starship.toml detected without settings.json - preserve as is
    Write-Host "Existing Starship configuration detected and preserved." -ForegroundColor Green
} else {
    # Fresh install: Apply default Nirmana signature theme
    $sourceNirmanaTheme = Join-Path $installDir "themes\nirmana.toml"
    if (Test-Path $sourceNirmanaTheme) {
        Copy-Item $sourceNirmanaTheme $starshipConfigPath -Force
        Write-Host "Nirmana signature theme applied successfully." -ForegroundColor Green
    } else {
        $remoteThemeUrl = "https://raw.githubusercontent.com/Andndre/nirmana-shell/main/themes/nirmana.toml"
        try {
            Invoke-RestMethod -Uri $remoteThemeUrl -OutFile $starshipConfigPath
            Write-Host "Nirmana signature theme downloaded and applied." -ForegroundColor Green
        } catch {
            Write-Host "Note: Default Starship configuration used." -ForegroundColor DarkGray
        }
    }
    # Record initial theme in settings.json
    try {
        if (!(Test-Path $nirmanaConfigDir)) { New-Item -ItemType Directory -Path $nirmanaConfigDir -Force | Out-Null }
        $initSettings = [pscustomobject]@{ theme = "nirmana"; predictionViewStyle = "InlineView" }
        $initJson = $initSettings | ConvertTo-Json -Depth 4
        [System.IO.File]::WriteAllText($nirmanaConfigFile, $initJson, [System.Text.UTF8Encoding]::new($false))
    } catch {}
}

# 5. PowerShell 7 Profile Configuration
Write-Host "`n[5/6] Setting Up PowerShell 7 Profile ($PROFILE)..." -ForegroundColor Cyan
$docsFolder = [Environment]::GetFolderPath('MyDocuments')
$ps7Dir = Join-Path $docsFolder "PowerShell"

if (!(Test-Path $ps7Dir)) {
    New-Item -ItemType Directory -Path $ps7Dir -Force | Out-Null
}

$ps7ProfilePath = Join-Path $ps7Dir "Microsoft.PowerShell_profile.ps1"
$ps7ProfileOrig = "$ps7ProfilePath.orig"
if (Test-Path $ps7ProfilePath) {
    if (-not (Test-Path $ps7ProfileOrig)) {
        $existingContent = Get-Content $ps7ProfilePath -Raw -ErrorAction SilentlyContinue
        if ($existingContent -and $existingContent -notmatch 'Nirmana-Shell') {
            Copy-Item $ps7ProfilePath $ps7ProfileOrig -Force
            Write-Host "Pristine original profile preserved at $ps7ProfileOrig" -ForegroundColor DarkGray
        }
    }
    Copy-Item $ps7ProfilePath "$ps7ProfilePath.bak" -Force
    Write-Host "Existing profile backed up to $ps7ProfilePath.bak" -ForegroundColor DarkGray
}

$sourceProfile = Join-Path $installDir "configs\Microsoft.PowerShell_profile.ps1"
if (Test-Path $sourceProfile) {
    Copy-Item $sourceProfile $ps7ProfilePath -Force
    Write-Host "PowerShell 7 profile installed successfully." -ForegroundColor Green
} else {
    $remoteProfileUrl = "https://raw.githubusercontent.com/Andndre/nirmana-shell/main/configs/Microsoft.PowerShell_profile.ps1"
    try {
        Invoke-RestMethod -Uri $remoteProfileUrl -OutFile $ps7ProfilePath
        Write-Host "PowerShell 7 profile downloaded and installed." -ForegroundColor Green
    } catch {
        Write-Host "Failed to download remote profile: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Create user custom extension template if not present
$userCustomProfile = Join-Path $nirmanaConfigDir "custom.ps1"
if (!(Test-Path $userCustomProfile)) {
    if (!(Test-Path $nirmanaConfigDir)) { New-Item -ItemType Directory -Path $nirmanaConfigDir -Force | Out-Null }
    $customTemplate = @'
# Nirmana-Shell: User Custom Extensions
# Add your personal functions, aliases, and environment variables here.
# This file is NEVER overwritten during Nirmana-Shell updates.

# Examples:
# function proj { Set-Location D:\projects }
# $env:EDITOR = 'code'
'@
    Set-Content -Path $userCustomProfile -Value $customTemplate -Encoding utf8
}

# Notification bridge for Windows PowerShell 5.1
$ps5Dir = Join-Path $docsFolder "WindowsPowerShell"
if (!(Test-Path $ps5Dir)) {
    New-Item -ItemType Directory -Path $ps5Dir -Force | Out-Null
}
$ps5ProfilePath = Join-Path $ps5Dir "Microsoft.PowerShell_profile.ps1"
if (!(Test-Path $ps5ProfilePath)) {
    $ps5Bridge = @'
# Nirmana-Shell: Legacy PowerShell Notification
if (Get-Command pwsh -ErrorAction SilentlyContinue) {
    Write-Host "`n[Nirmana-Shell] Running Windows PowerShell 5.1. Type 'pwsh' to switch to PowerShell 7.`n" -ForegroundColor DarkCyan
}
'@
    Set-Content -Path $ps5ProfilePath -Value $ps5Bridge -Encoding utf8
}

# 6. Windows Terminal Settings (Silence Bell, Font, Schemes, & PS7 Default)
Write-Host "`n[6/6] Configuring Windows Terminal (Bell, Font, Schemes & PS7 Default)..." -ForegroundColor Cyan
$wtSettingsPaths = @(
    "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json",
    "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json",
    "$env:LOCALAPPDATA\Microsoft\Windows Terminal\settings.json"
)

$schemesToInject = @'
    {
      "name": "Dracula",
      "background": "#282A36",
      "foreground": "#F8F8F2",
      "cursorColor": "#F8F8F2",
      "selectionBackground": "#44475A",
      "black": "#21222C",
      "red": "#FF5555",
      "green": "#50FA7B",
      "yellow": "#F1FA8C",
      "blue": "#BD93F9",
      "purple": "#FF79C6",
      "cyan": "#8BE9FD",
      "white": "#F8F8F2",
      "brightBlack": "#6272A4",
      "brightRed": "#FF6E6E",
      "brightGreen": "#69FF94",
      "brightYellow": "#FFFFA5",
      "brightBlue": "#D6ACFF",
      "brightPurple": "#FF92DF",
      "brightCyan": "#A4FFFF",
      "brightWhite": "#FFFFFF"
    },
    {
      "name": "Catppuccin Mocha",
      "background": "#1E1E2E",
      "foreground": "#CDD6F4",
      "cursorColor": "#F5E0DC",
      "selectionBackground": "#585B70",
      "black": "#45475A",
      "red": "#F38BA8",
      "green": "#A6E3A1",
      "yellow": "#F9E2AF",
      "blue": "#89B4FA",
      "purple": "#F5C2E7",
      "cyan": "#94E2D5",
      "white": "#BAC2DE",
      "brightBlack": "#585B70",
      "brightRed": "#F38BA8",
      "brightGreen": "#A6E3A1",
      "brightYellow": "#F9E2AF",
      "brightBlue": "#89B4FA",
      "brightPurple": "#F5C2E7",
      "brightCyan": "#94E2D5",
      "brightWhite": "#A6ADC8"
    },
    {
      "name": "Tokyo Night",
      "background": "#1A1B26",
      "foreground": "#C0CAF5",
      "cursorColor": "#C0CAF5",
      "selectionBackground": "#33467C",
      "black": "#15161E",
      "red": "#F7768E",
      "green": "#9ECE6A",
      "yellow": "#E0AF68",
      "blue": "#7AA2F7",
      "purple": "#BB9AF7",
      "cyan": "#7DCFFF",
      "white": "#A9B1D6",
      "brightBlack": "#414868",
      "brightRed": "#F7768E",
      "brightGreen": "#9ECE6A",
      "brightYellow": "#E0AF68",
      "brightBlue": "#7AA2F7",
      "brightPurple": "#BB9AF7",
      "brightCyan": "#7DCFFF",
      "brightWhite": "#C0CAF5"
    },
    {
      "name": "Nirmana",
      "background": "#12141A",
      "foreground": "#F8F9FA",
      "cursorColor": "#00F0FF",
      "selectionBackground": "#2E3440",
      "black": "#1E222D",
      "red": "#FF4757",
      "green": "#2ED573",
      "yellow": "#FED330",
      "blue": "#00F0FF",
      "purple": "#A29BFE",
      "cyan": "#00F0FF",
      "white": "#F8F9FA",
      "brightBlack": "#57606F",
      "brightRed": "#FF6B81",
      "brightGreen": "#7BED9F",
      "brightYellow": "#FFEAA7",
      "brightBlue": "#70A1FF",
      "brightPurple": "#C56CF0",
      "brightCyan": "#00D2D3",
      "brightWhite": "#FFFFFF"
    }
'@

foreach ($wtPath in $wtSettingsPaths) {
    if (Test-Path $wtPath) {
        try {
            $raw = Get-Content $wtPath -Raw -Encoding utf8
            if ($raw -notmatch '"Catppuccin Mocha"' -and $raw -match '("schemes"\s*:\s*\[)') {
                $raw = $raw -replace '("schemes"\s*:\s*\[)', "`$1`n$schemesToInject,"
            } elseif ($raw -notmatch '"Dracula"' -and $raw -match '("schemes"\s*:\s*\[)') {
                $raw = $raw -replace '("schemes"\s*:\s*\[)', "`$1`n$schemesToInject,"
            }
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
            }
            $targetScheme = if ($savedTheme -and $themeToWtScheme.ContainsKey($savedTheme)) {
                $themeToWtScheme[$savedTheme]
            } else {
                $null
            }

            # Safely target profiles.defaults block without mutating custom profiles (e.g. WSL, CMD)
            try {
                $jsonObj = $raw | ConvertFrom-Json
                if ($jsonObj.profiles.defaults) {
                    if ($targetScheme) {
                        $jsonObj.profiles.defaults.colorScheme = $targetScheme
                    }
                    if (-not $jsonObj.profiles.defaults.font -or $jsonObj.profiles.defaults.font.face -ne 'CaskaydiaCove NF') {
                        $jsonObj.profiles.defaults.font = [pscustomobject]@{ face = 'CaskaydiaCove NF' }
                    }
                    $jsonObj.profiles.defaults.bellStyle = 'none'
                    $raw = $jsonObj | ConvertTo-Json -Depth 10
                }
            } catch {
                if ($raw -match '("defaults"\s*:\s*\{[\s\S]*?\n\s*\})(?=\s*,\s*("list"|\}))') {
                    $defaultsBlock = $Matches[1]
                    $updatedDefaults = $defaultsBlock

                    if ($targetScheme) {
                        if ($updatedDefaults -match '("colorScheme"\s*:\s*)"[^"]*"') {
                            $updatedDefaults = [regex]::new('("colorScheme"\s*:\s*)"[^"]*"').Replace($updatedDefaults, "`$1`"$targetScheme`"", 1)
                        } else {
                            $updatedDefaults = $updatedDefaults -replace '("defaults"\s*:\s*\{)', "`$1`n      `"colorScheme`": `"$targetScheme`","
                        }
                    }

                    if ($updatedDefaults -notmatch '"face"\s*:\s*"CaskaydiaCove NF"') {
                        if ($updatedDefaults -match '("font"\s*:\s*\{[\s\S]*?\})') {
                            $fontBlock = $Matches[1]
                            $newFontBlock = $fontBlock -replace '("face"\s*:\s*)"[^"]*"', '$1"CaskaydiaCove NF"'
                            if ($fontBlock -notmatch '"face"') {
                                $newFontBlock = $fontBlock -replace '("font"\s*:\s*\{)', '$1`n        "face": "CaskaydiaCove NF",'
                            }
                            $updatedDefaults = $updatedDefaults.Replace($fontBlock, $newFontBlock)
                        } else {
                            $updatedDefaults = $updatedDefaults -replace '("defaults"\s*:\s*\{)', "`$1`n      `"font`": { `"face`": `"CaskaydiaCove NF`" },"
                        }
                    }

                    if ($updatedDefaults -match '("bellStyle"\s*:\s*)"[^"]*"') {
                        $updatedDefaults = [regex]::new('("bellStyle"\s*:\s*)"[^"]*"').Replace($updatedDefaults, '$1"none"', 1)
                    } else {
                        $updatedDefaults = $updatedDefaults -replace '("defaults"\s*:\s*\{)', "`$1`n      `"bellStyle`": `"none`","
                    }

                    $raw = $raw.Replace($defaultsBlock, $updatedDefaults)
                }
            }

            # Set PowerShell 7 as defaultProfile in Windows Terminal
            try {
                $jsonObj = $raw | ConvertFrom-Json
                $ps7Profile = $jsonObj.profiles.list | Where-Object {
                    $_.source -eq 'Windows.Terminal.PowershellCore' -or
                    $_.commandline -like '*pwsh*' -or
                    ($_.name -eq 'PowerShell' -and $_.guid -ne '{61c54bbd-c2c6-5271-96e7-009a87ff44bf}')
                } | Select-Object -First 1

                if ($ps7Profile -and $ps7Profile.guid) {
                    $ps7Guid = $ps7Profile.guid
                    if ($raw -match '"defaultProfile"\s*:\s*"[^"]*"') {
                        $raw = $raw -replace '("defaultProfile"\s*:\s*)"[^"]*"', "`$1`"$ps7Guid`""
                    }
                }
            } catch {}

            Set-Content -Path $wtPath -Value $raw -Encoding utf8
            Write-Host "Windows Terminal settings configured successfully at: $(Split-Path $wtPath -Leaf)" -ForegroundColor Green
        } catch {
            Write-Host "Note: Windows Terminal settings could not be modified automatically ($($_.Exception.Message))." -ForegroundColor DarkGray
        }
    }
}

Write-Host ""
Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Green
Write-Host "│            NIRMANA-SHELL INSTALLATION COMPLETE              │" -ForegroundColor Green
Write-Host "├─────────────────────────────────────────────────────────────┤" -ForegroundColor Cyan
Write-Host "│  Next Steps:                                                │" -ForegroundColor Yellow
Write-Host "│  1. Ensure a Nerd Font is selected (e.g. CaskaydiaCove NF)  │" -ForegroundColor White
if ($isLegacyPS) {
Write-Host "│  2. You are in PS 5.1: Type 'pwsh' to launch PowerShell 7   │" -ForegroundColor Yellow
} else {
Write-Host "│  2. Open a new tab in Windows Terminal to use PowerShell 7  │" -ForegroundColor White
}
Write-Host "│  3. Type 'nirmana theme' to launch the theme switcher       │" -ForegroundColor White
Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Green
Write-Host ""
