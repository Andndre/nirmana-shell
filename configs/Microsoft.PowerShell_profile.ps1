# =====================================================================
# Nirmana-Shell: PowerShell 7 Profile
# =====================================================================

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 1. Starship Prompt Engine
if (Get-Command starship -ErrorAction SilentlyContinue) {
    Invoke-Expression (&starship init powershell)
}

# 2. Global TUI Defaults (Rounded Borders & Indicators)
if (Get-Command fzf -ErrorAction SilentlyContinue) {
    $env:FZF_DEFAULT_OPTS = "--border=rounded --pointer='◆ ' --marker='✓ ' --scrollbar='│' --prompt='❯ '"
}

# 3. PSReadLine (Modern Autocomplete & Predictive IntelliSense)
if (Get-Module -ListAvailable PSReadLine) {
    Import-Module PSReadLine

    # Disable audio bell chime on backspace at beginning of line
    Set-PSReadLineOption -BellStyle None

    # Inline predictions (active only in VT-supported interactive consoles)
    if (-not [System.Console]::IsOutputRedirected) {
        Set-PSReadLineOption -PredictionSource History -ErrorAction SilentlyContinue
        Set-PSReadLineOption -PredictionViewStyle InlineView -ErrorAction SilentlyContinue
        Set-PSReadLineOption -Colors @{ InlinePrediction = '#767676' } -ErrorAction SilentlyContinue
    }

    # Key Handlers:
    # - Tab: Interactive menu completion grid
    Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete

    # - Ctrl+f: Accept prediction word-by-word (Fish style)
    Set-PSReadLineKeyHandler -Chord 'Ctrl+f' -Function ForwardWord

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
    switch ($SubCommand) {
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
            $tools = @('pwsh', 'starship', 'zoxide', 'eza', 'fzf', 'delta', 'fd', 'rg')
            $w = 70
            $line = '─' * ($w - 2)
            Write-Host ""
            Write-Host "╭$line╮" -ForegroundColor Cyan
            Write-Host "│                      NIRMANA HEALTH CHECK                          │" -ForegroundColor Cyan
            Write-Host "├$line┤" -ForegroundColor Cyan
            foreach ($t in $tools) {
                $found = Get-Command $t -ErrorAction SilentlyContinue
                if ($found) {
                    $label = "  [+] " + $t.PadRight(10)
                    $rem = $w - 2 - $label.Length - 1 - $found.Source.Length
                    if ($rem -lt 0) {
                        $truncated = "..." + $found.Source.Substring($found.Source.Length - ($w - 2 - $label.Length - 4))
                        Write-Host ("│" + $label + $truncated + " │") -ForegroundColor Green
                    } else {
                        Write-Host ("│" + $label + $found.Source + (' ' * $rem) + "│") -ForegroundColor Green
                    }
                } else {
                    $label = "  [-] " + $t.PadRight(10) + "Not found in PATH"
                    $rem = $w - 2 - $label.Length
                    Write-Host ("│" + $label + (' ' * [math]::Max(0, $rem)) + "│") -ForegroundColor Red
                }
            }
            Write-Host "╰$line╯" -ForegroundColor Cyan
            Write-Host ""
        }
        'reload' {
            . $PROFILE
            Write-Host ""
            Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Green
            Write-Host "│  PowerShell 7 profile reloaded successfully.                │" -ForegroundColor Green
            Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Green
            Write-Host ""
        }
        default {
            Write-Host ""
            Write-Host "╭─────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
            Write-Host "│                      NIRMANA-SHELL CLI                      │" -ForegroundColor Cyan
            Write-Host "├─────────────────────────────────────────────────────────────┤" -ForegroundColor Cyan
            Write-Host "│  Usage: nirmana <command> [arguments]                       │" -ForegroundColor White
            Write-Host "│                                                             │" -ForegroundColor White
            Write-Host "│  Commands:                                                  │" -ForegroundColor Yellow
            Write-Host "│    theme [name]   Switch theme with top-preview TUI         │" -ForegroundColor White
            Write-Host "│    update         Update Nirmana-Shell from GitHub          │" -ForegroundColor White
            Write-Host "│    doctor         Verify health and PATH of all CLI tools   │" -ForegroundColor White
            Write-Host "│    reload         Reload PowerShell 7 profile               │" -ForegroundColor White
            Write-Host "╰─────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
            Write-Host ""
        }
    }
}
Set-Alias -Name nirmana -Value nirmana-shell -Option AllScope -Scope Global -Force

# Argument completer for nirmana-shell
Register-ArgumentCompleter -Native -CommandName 'nirmana-shell', 'nirmana' -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    $subcommands = @('theme', 'update', 'doctor', 'reload')
    $elements = $commandAst.CommandElements
    if ($elements.Count -eq 2) {
        $subcommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
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
