<#
.SYNOPSIS
    Nirmana-Shell: Automated Modern Terminal Setup for Windows
.DESCRIPTION
    Installs modern CLI tools (PowerShell 7, Git, Starship, Zoxide, Eza, FZF, Delta, FD),
    configures optimized PowerShell 7 profile, sets Nirmana signature theme,
    disables terminal alert bell beeps, and optimizes Git diffs.
.USAGE
    irm https://raw.githubusercontent.com/Andndre/nirmana-shell/main/setup.ps1 | iex
#>

$ErrorActionPreference = 'Stop'

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$setupScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$versionFile = if ($setupScriptDir) { Join-Path $setupScriptDir "VERSION" } else { $null }
$nirmanaVer = if ($versionFile -and (Test-Path $versionFile)) { (Get-Content $versionFile -Raw).Trim() } else { "1.0.0" }

Write-Host ""
Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
Write-Host "│      NIRMANA-SHELL: MODERN TERMINAL AUTOMATION (v$nirmanaVer)     │" -ForegroundColor White
Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
Write-Host ""

# 1. Package Installation via WinGet
Write-Host "[1/6] Checking & Installing Modern CLI Tools via WinGet..." -ForegroundColor Cyan
$packages = @(
    "Microsoft.PowerShell",
    "Git.Git",
    "Starship.Starship",
    "ajeetdsouza.zoxide",
    "eza-community.eza",
    "junegunn.fzf",
    "dandavison.delta",
    "sharkdp.fd"
)

foreach ($pkg in $packages) {
    Write-Host "--> Checking $pkg..." -NoNewline
    $installed = winget list --id $pkg --exact --accept-source-agreements 2>$null
    if ($LASTEXITCODE -eq 0 -and ($installed | Out-String) -match $pkg) {
        Write-Host " [Installed]" -ForegroundColor Green
    } else {
        Write-Host " [Installing...]" -ForegroundColor Yellow
        winget install --id $pkg --source winget --accept-source-agreements --accept-package-agreements --silent
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
            git -C $installDir pull --quiet
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
}

# 4. Starship Config (Default: Nirmana Theme)
Write-Host "`n[4/6] Setting Up Starship Configuration (~/.config/starship.toml)..." -ForegroundColor Cyan
$starshipConfigDir = Join-Path $HOME ".config"
if (!(Test-Path $starshipConfigDir)) {
    New-Item -ItemType Directory -Path $starshipConfigDir -Force | Out-Null
}

$starshipConfigPath = Join-Path $starshipConfigDir "starship.toml"
if (Test-Path $starshipConfigPath) {
    Copy-Item $starshipConfigPath "$starshipConfigPath.bak" -Force
}

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

# 5. PowerShell 7 Profile Configuration
Write-Host "`n[5/6] Setting Up PowerShell 7 Profile ($PROFILE)..." -ForegroundColor Cyan
$docsFolder = [Environment]::GetFolderPath('MyDocuments')
$ps7Dir = Join-Path $docsFolder "PowerShell"

if (!(Test-Path $ps7Dir)) {
    New-Item -ItemType Directory -Path $ps7Dir -Force | Out-Null
}

$ps7ProfilePath = Join-Path $ps7Dir "Microsoft.PowerShell_profile.ps1"
if (Test-Path $ps7ProfilePath) {
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

# 6. Windows Terminal Settings (Silence Bell, Font, Schemes, & PS7 Default)
Write-Host "`n[6/6] Configuring Windows Terminal (Bell, Font, Schemes & PS7 Default)..." -ForegroundColor Cyan
$wtSettingsPaths = @(
    "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json",
    "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json",
    "$env:LOCALAPPDATA\Microsoft\Windows Terminal\settings.json"
)

$schemesToInject = @'
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
            }
            if ($raw -match '"colorScheme"\s*:\s*"[^"]*"') {
                $raw = $raw -replace '("colorScheme"\s*:\s*)"[^"]*"', '$1"Catppuccin Mocha"'
            } elseif ($raw -match '("defaults"\s*:\s*\{)') {
                $raw = $raw -replace '("defaults"\s*:\s*\{)', "`$1`n      `"colorScheme`": `"Catppuccin Mocha`","
            }
            if ($raw -notmatch '"face"\s*:\s*"CaskaydiaCove NF"' -and $raw -match '("defaults"\s*:\s*\{)') {
                $raw = $raw -replace '("defaults"\s*:\s*\{)', "`$1`n      `"font`": { `"face`": `"CaskaydiaCove NF`" },"
            }
            if ($raw -match '"bellStyle"\s*:\s*"[^"]*"') {
                $raw = $raw -replace '("bellStyle"\s*:\s*)"[^"]*"', '$1"none"'
            } elseif ($raw -match '("defaults"\s*:\s*\{)') {
                $raw = $raw -replace '("defaults"\s*:\s*\{)', "`$1`n      `"bellStyle`": `"none`","
            }
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
Write-Host "│  2. Open a new tab in Windows Terminal to use PowerShell 7  │" -ForegroundColor White
Write-Host "│  3. Type 'nirmana theme' to launch the theme switcher       │" -ForegroundColor White
Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Green
Write-Host ""
