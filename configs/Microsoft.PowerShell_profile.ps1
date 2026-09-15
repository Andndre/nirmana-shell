# =====================================================================
# Nirmana-Shell: PowerShell 7 Profile
# =====================================================================

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 1. Starship Prompt Engine
if (Get-Command starship -ErrorAction SilentlyContinue) {
    $starshipConfigPath = Join-Path $HOME ".config\starship.toml"
    if ($env:STARSHIP_CONFIG -and -not (Test-Path $env:STARSHIP_CONFIG)) {
        Remove-Item Env:\STARSHIP_CONFIG -ErrorAction SilentlyContinue
    }
    if (Test-Path $starshipConfigPath) {
        $env:STARSHIP_CONFIG = $starshipConfigPath
    }
    Invoke-Expression (&starship init powershell)
}

# 2. Global TUI Defaults (Rounded Borders & Indicators)
if (Get-Command fzf -ErrorAction SilentlyContinue) {
    $env:FZF_DEFAULT_OPTS = "--border=rounded --pointer='◆ ' --marker='✓ ' --scrollbar='│' --prompt='❯ '"
}

# Nirmana state & preferences management (~/.config/nirmana/settings.json)
$script:nirmanaConfigDir = Join-Path $HOME ".config\nirmana"
$script:nirmanaConfigFile = Join-Path $script:nirmanaConfigDir "settings.json"

function script:Get-NirmanaConfig {
    if (Test-Path $script:nirmanaConfigFile) {
        try {
            return (Get-Content $script:nirmanaConfigFile -Raw -Encoding utf8 | ConvertFrom-Json)
        } catch {
            return [pscustomobject]@{}
        }
    }
    return [pscustomobject]@{}
}

function script:Set-NirmanaConfig {
    param([string]$Key, [object]$Value)
    try {
        if (!(Test-Path $script:nirmanaConfigDir)) {
            New-Item -ItemType Directory -Path $script:nirmanaConfigDir -Force | Out-Null
        }
        $cfg = script:Get-NirmanaConfig
        if ($cfg.PSObject.Properties[$Key]) {
            $cfg.$Key = $Value
        } else {
            $cfg | Add-Member -NotePropertyName $Key -NotePropertyValue $Value -Force
        }
        $json = $cfg | ConvertTo-Json -Depth 4
        [System.IO.File]::WriteAllText($script:nirmanaConfigFile, $json, [System.Text.UTF8Encoding]::new($false))
    } catch {}
}

# 3. PSReadLine (Modern Autocomplete & Predictive IntelliSense)
if ((Get-Module -Name PSReadLine -ErrorAction SilentlyContinue) -or (Import-Module PSReadLine -ErrorAction SilentlyContinue)) {

    # Disable audio bell chime on backspace at beginning of line
    Set-PSReadLineOption -BellStyle None

    # Load persisted prediction view style or default to InlineView
    $savedCfg = script:Get-NirmanaConfig
    $savedView = if ($savedCfg.predictionViewStyle -eq "ListView") { "ListView" } else { "InlineView" }

    # Inline predictions (active only in VT-supported interactive consoles)
    if (-not [System.Console]::IsOutputRedirected) {
        Set-PSReadLineOption -PredictionSource History -ErrorAction SilentlyContinue
        Set-PSReadLineOption -PredictionViewStyle $savedView -ErrorAction SilentlyContinue
        Set-PSReadLineOption -Colors @{ InlinePrediction = '#767676' } -ErrorAction SilentlyContinue
    }

    # Key Handlers:
    # - Tab: Interactive menu completion grid
    Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete

    # - Ctrl+f: Accept prediction word-by-word (Fish style)
    Set-PSReadLineKeyHandler -Chord 'Ctrl+f' -Function ForwardWord

    # - F2: Toggle between InlineView and ListView and persist preference
    Set-PSReadLineKeyHandler -Key F2 -ScriptBlock {
        param($key, $arg)
        try {
            [Microsoft.PowerShell.PSConsoleReadLine]::SwitchPredictionView($key, $arg)
        } catch {
            $curr = (Get-PSReadLineOption).PredictionViewStyle
            $next = if ($curr -eq 'ListView') { 'InlineView' } else { 'ListView' }
            Set-PSReadLineOption -PredictionViewStyle $next -ErrorAction SilentlyContinue
        }
        try {
            $actual = (Get-PSReadLineOption).PredictionViewStyle.ToString()
            script:Set-NirmanaConfig "predictionViewStyle" $actual
        } catch {}
    }

    # - Ctrl+r: Interactive Fuzzy History Search via fzf with rounded TUI border
    if (Get-Command fzf -ErrorAction SilentlyContinue) {
        Set-PSReadLineKeyHandler -Chord 'Ctrl+r' -ScriptBlock {
            $historyFile = (Get-PSReadLineOption).HistorySavePath
            if (Test-Path $historyFile) {
                $selected = Get-Content $historyFile -Encoding utf8 -ErrorAction SilentlyContinue |
                    fzf --tac --no-sort `
                        --border=rounded `
                        --border-label=" Command History Search (Ctrl+R) " `
                        --border-label-pos=3 `
                        --prompt="Search ❯ " `
                        --pointer="◆ " `
                        --scrollbar="│" `
                        --height=50% `
                        --reverse
                if ($selected) {
                    [Microsoft.PowerShell.PSConsoleReadLine]::RevertLine()
                    [Microsoft.PowerShell.PSConsoleReadLine]::Insert($selected)
                }
            }
        }
    }
}

# 4. Zoxide (Smarter 'cd' navigation via 'z' and 'zi')
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    $env:_ZO_FZF_OPTS = "--border=rounded --border-label=' Directory Jump (zi) ' --border-label-pos=3 --prompt='Jump ❯ ' --pointer='◆ ' --scrollbar='│' --height=50% --reverse"
    Invoke-Expression (&zoxide init powershell | Out-String)
    function global:za { zoxide add @args }
}

# 5. Eza (Modern 'ls' replacement with icons & colors)
if (Get-Command eza -ErrorAction SilentlyContinue) {
    if (Test-Path Alias:ls) { Remove-Item Alias:ls -Force }
    function ls { eza --icons=auto --group-directories-first @args }
    function ll { eza --icons=auto --group-directories-first -l @args }
    function la { eza --icons=auto --group-directories-first -la @args }
    function lt { eza --icons=auto --tree --level=2 @args }
}

# 6. Nirmana-Shell CLI Helper & Commands
function global:nirmana-shell {
    param(
        [Parameter(Position=0)]
        [string]$SubCommand,
        [Parameter(Position=1)]
        [string]$Argument
    )

    $root = Join-Path $HOME ".nirmana-shell"
    $versionFile = Join-Path $root "VERSION"
    $version = if (Test-Path $versionFile) { (Get-Content $versionFile -Raw).Trim() } else { "1.0.0" }

    switch ($SubCommand) {
        'version' {
            $gitCommit = $null
            if (Test-Path (Join-Path $root ".git")) {
                try { $gitCommit = (git -C $root rev-parse --short HEAD 2>$null).Trim() } catch {}
            }
            $commitStr = if ($gitCommit) { " (commit $gitCommit)" } else { "" }
            $osDesc = [System.Runtime.InteropServices.RuntimeInformation]::OSDescription
            Write-Host ""
            Write-Host "nirmana-shell v$version$commitStr" -ForegroundColor Cyan
            Write-Host "PowerShell $($PSVersionTable.PSVersion) on $osDesc" -ForegroundColor Gray
            Write-Host ""
        }
        '-v' { & nirmana-shell version }
        '--version' { & nirmana-shell version }
        'theme' {
            $switchScript = Join-Path $root "switch-theme.ps1"
            if (Test-Path $switchScript) {
                & $switchScript $Argument
            } else {
                Write-Error "Theme switch script not found at $root"
            }
        }
        'update' {
            if (Test-Path (Join-Path $root ".git")) {
                Write-Host "Updating Nirmana-Shell from GitHub..." -ForegroundColor Cyan
                git -C $root fetch --quiet origin main
                git -C $root reset --hard origin/main
                & (Join-Path $root "setup.ps1")
            } else {
                Write-Host "Re-running Nirmana-Shell setup..." -ForegroundColor Cyan
                irm https://raw.githubusercontent.com/Andndre/nirmana-shell/main/setup.ps1 | iex
            }
        }
        'doctor' {
            $toolDefinitions = [ordered]@{
                'pwsh'     = @{ Id = 'Microsoft.PowerShell'; Source = 'winget'; Name = 'PowerShell 7' }
                'starship' = @{ Id = 'Starship.Starship'; Source = 'winget'; Name = 'Starship Prompt' }
                'zoxide'   = @{ Id = 'ajeetdsouza.zoxide'; Source = 'winget'; Name = 'Zoxide Jump' }
                'eza'      = @{ Id = 'eza-community.eza'; Source = 'winget'; Name = 'Eza File Lister' }
                'fzf'      = @{ Id = 'junegunn.fzf'; Source = 'winget'; Name = 'FZF Fuzzy Finder' }
                'delta'    = @{ Id = 'dandavison.delta'; Source = 'winget'; Name = 'Git Delta Pager' }
                'fd'       = @{ Id = 'sharkdp.fd'; Source = 'winget'; Name = 'FD File Search' }
                'rg'       = @{ Id = 'BurntSushi.ripgrep.MSVC'; Source = 'winget'; Name = 'Ripgrep Text Search' }
            }

            $w = 72
            $line = '─' * ($w - 2)
            $title = "NIRMANA HEALTH CHECK (v$version)"
            $padTotal = $w - 2 - $title.Length
            $padLeft = [math]::Max(0, [int]($padTotal / 2))
            $padRight = [math]::Max(0, $padTotal - $padLeft)
            Write-Host ""
            Write-Host "╭$line╮" -ForegroundColor Cyan
            Write-Host ("│" + (' ' * $padLeft) + $title + (' ' * $padRight) + "│") -ForegroundColor Cyan
            Write-Host "├$line┤" -ForegroundColor Cyan

            $missingTools = @()
            foreach ($entry in $toolDefinitions.GetEnumerator()) {
                $cmdName = $entry.Key
                $info = $entry.Value
                $found = Get-Command $cmdName -ErrorAction SilentlyContinue
                if ($found) {
                    $label = "  [+] " + $cmdName.PadRight(10)
                    $rem = $w - 2 - $label.Length - 1 - $found.Source.Length
                    if ($rem -lt 0) {
                        $truncated = "..." + $found.Source.Substring($found.Source.Length - ($w - 2 - $label.Length - 4))
                        Write-Host ("│" + $label + $truncated + " │") -ForegroundColor Green
                    } else {
                        Write-Host ("│" + $label + $found.Source + (' ' * $rem) + "│") -ForegroundColor Green
                    }
                } else {
                    $label = "  [-] " + $cmdName.PadRight(10) + "Not found in PATH"
                    $rem = $w - 2 - $label.Length
                    Write-Host ("│" + $label + (' ' * [math]::Max(0, $rem)) + "│") -ForegroundColor Red
                    $missingTools += $info
                }
            }

            # Check Nerd Font
            $fontDirs = @(
                "$env:LOCALAPPDATA\Microsoft\Windows\Fonts",
                "$env:WINDIR\Fonts"
            )
            $fontFound = $false
            foreach ($d in $fontDirs) {
                if (Test-Path $d) {
                    $ff = Get-ChildItem -Path $d -Filter "*Caskaydia*Nerd*.ttf" -ErrorAction SilentlyContinue
                    if (-not $ff) { $ff = Get-ChildItem -Path $d -Filter "*Caskaydia*NF*.ttf" -ErrorAction SilentlyContinue }
                    if ($ff) { $fontFound = $true; break }
                }
            }

            if ($fontFound) {
                $fontLabel = "  [+] Font      CaskaydiaCove NF installed"
                $fontRem = $w - 2 - $fontLabel.Length
                Write-Host ("│" + $fontLabel + (' ' * [math]::Max(0, $fontRem)) + "│") -ForegroundColor Green
            } else {
                $fontLabel = "  [-] Font      CaskaydiaCove NF missing"
                $fontRem = $w - 2 - $fontLabel.Length
                Write-Host ("│" + $fontLabel + (' ' * [math]::Max(0, $fontRem)) + "│") -ForegroundColor Yellow
            }

            Write-Host "╰$line╯" -ForegroundColor Cyan
            Write-Host ""

            if ($Argument -eq '--fix') {
                if ($missingTools.Count -eq 0 -and $fontFound) {
                    Write-Host "All CLI tools and fonts are already installed and healthy." -ForegroundColor Green
                } else {
                    Write-Host "Self-Healing: Installing missing components via WinGet..." -ForegroundColor Cyan
                    foreach ($m in $missingTools) {
                        Write-Host "--> Installing $($m.Name) ($($m.Id))..." -ForegroundColor Yellow
                        winget install --id $m.Id --source $m.Source --accept-source-agreements --accept-package-agreements --silent
                    }
                    if (-not $fontFound) {
                        Write-Host "--> Installing CaskaydiaCove Nerd Font..." -ForegroundColor Yellow
                        winget install --id ryanoasis.CaskaydiaCove --source winget-font --accept-source-agreements --accept-package-agreements --silent
                    }
                    Write-Host "`nSelf-healing complete. Please restart your terminal or run 'nirmana reload'." -ForegroundColor Green
                }
            } elseif ($missingTools.Count -gt 0 -or -not $fontFound) {
                Write-Host "Tip: Run 'nirmana doctor --fix' to automatically install missing tools and fonts." -ForegroundColor Yellow
                Write-Host ""
            }
        }
        'benchmark' {
            $w = 62
            $line = '─' * ($w - 2)
            $title = "NIRMANA STARTUP BENCHMARK"
            $padTotal = $w - 2 - $title.Length
            $padLeft = [math]::Max(0, [int]($padTotal / 2))
            $padRight = [math]::Max(0, $padTotal - $padLeft)

            Write-Host ""
            Write-Host "╭$line╮" -ForegroundColor Cyan
            Write-Host ("│" + (' ' * $padLeft) + $title + (' ' * $padRight) + "│") -ForegroundColor Cyan
            Write-Host "├$line┤" -ForegroundColor Cyan

            $benchmarks = [ordered]@{}

            # 1. Starship init
            $benchmarks['Starship Prompt'] = (Measure-Command {
                if (Get-Command starship -ErrorAction SilentlyContinue) {
                    & starship init powershell | Out-Null
                }
            }).TotalMilliseconds

            # 2. PSReadLine
            $benchmarks['PSReadLine Setup'] = (Measure-Command {
                Get-PSReadLineOption | Out-Null
            }).TotalMilliseconds

            # 3. Zoxide init
            $benchmarks['Zoxide Navigation'] = (Measure-Command {
                if (Get-Command zoxide -ErrorAction SilentlyContinue) {
                    & zoxide init powershell | Out-Null
                }
            }).TotalMilliseconds

            # 4. Settings read
            $benchmarks['Settings JSON'] = (Measure-Command {
                $cfgPath = Join-Path $HOME ".config\nirmana\settings.json"
                if (Test-Path $cfgPath) { Get-Content $cfgPath -Raw | Out-Null }
            }).TotalMilliseconds

            # 5. User custom profile
            $benchmarks['User Custom (custom.ps1)'] = (Measure-Command {
                $cPath = Join-Path $HOME ".config\nirmana\custom.ps1"
                if (Test-Path $cPath) { Get-Content $cPath -Raw | Out-Null }
            }).TotalMilliseconds

            $totalMs = 0
            foreach ($entry in $benchmarks.GetEnumerator()) {
                $ms = [math]::Round($entry.Value, 1)
                $totalMs += $ms
                $color = if ($ms -lt 30) { "Green" } elseif ($ms -lt 80) { "Yellow" } else { "Red" }

                $keyStr = "  " + $entry.Key
                $valStr = "$ms ms  "
                $spaceCount = ($w - 2) - $keyStr.Length - $valStr.Length
                $spaces = ' ' * [math]::Max(0, $spaceCount)

                Write-Host "│" -ForegroundColor Cyan -NoNewline
                Write-Host $keyStr -ForegroundColor White -NoNewline
                Write-Host $spaces -NoNewline
                Write-Host $valStr -ForegroundColor $color -NoNewline
                Write-Host "│" -ForegroundColor Cyan
            }

            $totalRounded = [math]::Round($totalMs, 1)
            $sumLabel = "  Estimated Profile Overhead:"
            $sumVal = "$totalRounded ms  "
            $sumSpaces = ' ' * [math]::Max(0, ($w - 2) - $sumLabel.Length - $sumVal.Length)

            Write-Host "├$line┤" -ForegroundColor Cyan
            Write-Host "│" -ForegroundColor Cyan -NoNewline
            Write-Host $sumLabel -ForegroundColor White -NoNewline
            Write-Host $sumSpaces -NoNewline
            Write-Host $sumVal -ForegroundColor Cyan -NoNewline
            Write-Host "│" -ForegroundColor Cyan
            Write-Host "╰$line╯" -ForegroundColor Cyan
            Write-Host ""
        }
        'reload' {
            $starshipConfigPath = Join-Path $HOME ".config\starship.toml"
            if (Test-Path $starshipConfigPath) {
                $env:STARSHIP_CONFIG = $starshipConfigPath
            } else {
                Remove-Item Env:\STARSHIP_CONFIG -ErrorAction SilentlyContinue
            }
            . $PROFILE
            Write-Host ""
            Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Green
            Write-Host "│  PowerShell 7 profile reloaded successfully.                │" -ForegroundColor Green
            Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Green
            Write-Host ""
        }
        'uninstall' {
            Write-Host ""
            Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Red
            Write-Host "│              NIRMANA-SHELL UNINSTALLATION                   │" -ForegroundColor Red
            Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Red
            Write-Host "This will:" -ForegroundColor Yellow
            Write-Host "  1. Remove Nirmana-Shell from PowerShell 7 profile (restoring original if available)"
            Write-Host "  2. Remove legacy PowerShell 5.1 notification bridge"
            Write-Host "  3. Remove ~/.nirmana-shell repository directory"
            Write-Host "  4. Remove ~/.config/nirmana configuration directory"
            Write-Host "  5. Unregister 'nirmana' command and aliases from active session"
            Write-Host ""
            $confirm = Read-Host "Are you sure you want to uninstall Nirmana-Shell? (y/N)"
            if ($confirm -match '^[Yy]$') {
                # 1. Purge PowerShell 7 profile across potential locations
                $profilesToCheck = @(
                    $PROFILE,
                    (Join-Path ([Environment]::GetFolderPath('MyDocuments')) "PowerShell\Microsoft.PowerShell_profile.ps1")
                ) | Select-Object -Unique

                foreach ($p in $profilesToCheck) {
                    if (Test-Path $p) {
                        $origFile = "$p.orig"
                        $bakFile = "$p.bak"
                        $restored = $false

                        if (Test-Path $origFile) {
                            $origRaw = Get-Content $origFile -Raw -ErrorAction SilentlyContinue
                            if ($origRaw -and $origRaw -notmatch 'Nirmana-Shell') {
                                Copy-Item $origFile $p -Force
                                $restored = $true
                                Write-Host "--> Restored pristine original profile from $origFile." -ForegroundColor Green
                            }
                            Remove-Item $origFile -Force -ErrorAction SilentlyContinue
                        }

                        if (-not $restored -and (Test-Path $bakFile)) {
                            $bakRaw = Get-Content $bakFile -Raw -ErrorAction SilentlyContinue
                            if ($bakRaw -and $bakRaw -notmatch 'Nirmana-Shell') {
                                Copy-Item $bakFile $p -Force
                                $restored = $true
                                Write-Host "--> Restored profile from $bakFile." -ForegroundColor Green
                            }
                            Remove-Item $bakFile -Force -ErrorAction SilentlyContinue
                        }

                        if (-not $restored) {
                            $currentRaw = Get-Content $p -Raw -ErrorAction SilentlyContinue
                            if ($currentRaw -match 'Nirmana-Shell') {
                                Remove-Item $p -Force -ErrorAction SilentlyContinue
                                Write-Host "--> Removed Nirmana-Shell profile: $p" -ForegroundColor Green
                            }
                        }
                    }
                    Remove-Item "$p.orig", "$p.bak" -Force -ErrorAction SilentlyContinue
                }

                # 2. Remove Windows PowerShell 5.1 notification bridge
                $ps5Profile = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "WindowsPowerShell\Microsoft.PowerShell_profile.ps1"
                if (Test-Path $ps5Profile) {
                    $ps5Raw = Get-Content $ps5Profile -Raw -ErrorAction SilentlyContinue
                    if ($ps5Raw -match 'Nirmana-Shell') {
                        Remove-Item $ps5Profile -Force -ErrorAction SilentlyContinue
                        Write-Host "--> Removed PS 5.1 notification bridge: $ps5Profile" -ForegroundColor Green
                    }
                }

                # 3. Remove ~/.nirmana-shell repository directory
                $nirmanaHome = Join-Path $HOME ".nirmana-shell"
                if (Test-Path $nirmanaHome) {
                    Remove-Item $nirmanaHome -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Host "--> Removed $nirmanaHome." -ForegroundColor Green
                }

                # 4. Remove ~/.config/nirmana directory
                $nirmanaCfg = Join-Path $HOME ".config\nirmana"
                if (Test-Path $nirmanaCfg) {
                    Remove-Item $nirmanaCfg -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Host "--> Removed $nirmanaCfg." -ForegroundColor Green
                }

                # 5. Purge aliases and functions from active in-memory session
                Remove-Alias -Name nirmana -Force -Scope Global -ErrorAction SilentlyContinue
                Remove-Item 'Alias:\nirmana' -Force -ErrorAction SilentlyContinue
                Remove-Item 'Function:\nirmana-shell' -Force -ErrorAction SilentlyContinue
                Remove-Item 'Function:\nirmana' -Force -ErrorAction SilentlyContinue
                Remove-Item 'Alias:\ls', 'Alias:\ll', 'Alias:\la', 'Alias:\lt' -Force -ErrorAction SilentlyContinue

                # Restore original profile if available; otherwise reset prompt to default
                $restoredProfile = $profilesToCheck | Where-Object { (Test-Path $_) -and ((Get-Content $_ -Raw -ErrorAction SilentlyContinue) -notmatch 'Nirmana-Shell') } | Select-Object -First 1
                if ($restoredProfile) {
                    try {
                        . $restoredProfile
                        Write-Host "--> Restored profile reloaded into active session." -ForegroundColor Green
                    } catch {}
                } else {
                    function global:prompt {
                        "PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) "
                    }
                }

                Write-Host ""
                Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Green
                Write-Host "│  Nirmana-Shell has been completely uninstalled.             │" -ForegroundColor Green
                Write-Host "│  Commands and profile associations have been purged.        │" -ForegroundColor Green
                Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Green
                Write-Host ""
            } else {
                Write-Host "Uninstallation cancelled." -ForegroundColor Yellow
            }
        }
        default {
            Write-Host ""
            Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
            Write-Host "│                      NIRMANA-SHELL CLI                      │" -ForegroundColor Cyan
            Write-Host "├─────────────────────────────────────────────────────────────┤" -ForegroundColor Cyan
            Write-Host "│  Usage: nirmana <command> [arguments]                       │" -ForegroundColor White
            Write-Host "│                                                             │" -ForegroundColor White
            Write-Host "│  Commands:                                                  │" -ForegroundColor Yellow
            Write-Host "│    theme [name]     Switch theme with top-preview TUI       │" -ForegroundColor White
            Write-Host "│    version          Display version and system info         │" -ForegroundColor White
            Write-Host "│    update           Update Nirmana-Shell from GitHub        │" -ForegroundColor White
            Write-Host "│    doctor [--fix]   Verify and self-heal CLI dependencies   │" -ForegroundColor White
            Write-Host "│    benchmark        Profile shell startup latency           │" -ForegroundColor White
            Write-Host "│    reload           Reload PowerShell 7 profile             │" -ForegroundColor White
            Write-Host "│    uninstall        Cleanly remove Nirmana & restore backup │" -ForegroundColor White
            Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
            Write-Host ""
        }
    }
}
Set-Alias -Name nirmana -Value nirmana-shell -Option AllScope -Scope Global -Force

# Argument completer for nirmana-shell
Register-ArgumentCompleter -Native -CommandName 'nirmana-shell', 'nirmana' -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    $subcommands = @('theme', 'version', 'update', 'doctor', 'benchmark', 'reload', 'uninstall')
    $elements = $commandAst.CommandElements
    if ($elements.Count -eq 2) {
        $subcommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
    } elseif ($elements.Count -eq 3 -and $elements[1].Value -eq 'doctor') {
        @('--fix') | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
    } elseif ($elements.Count -eq 3 -and $elements[1].Value -eq 'theme') {
        $root = Join-Path $HOME ".nirmana-shell"
        $themes = @()
        if (Test-Path (Join-Path $root "themes")) {
            $themes += Get-ChildItem (Join-Path $root "themes") -Filter "*.toml" | ForEach-Object { $_.BaseName }
        }
        if (Get-Command starship -ErrorAction SilentlyContinue) {
            try { $themes += & starship preset --list 2>$null } catch {}
        }
        $themes | Select-Object -Unique | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
    }
}

# 7. Optional User Custom Extensions (~/.config/nirmana/custom.ps1)
$userCustomProfile = Join-Path $HOME ".config\nirmana\custom.ps1"
if (Test-Path $userCustomProfile) {
    try {
        . $userCustomProfile
    } catch {
        Write-Warning "[Nirmana-Shell] Error loading custom extensions (~/.config/nirmana/custom.ps1): $($_.Exception.Message)"
    }
}
