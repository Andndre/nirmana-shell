# =====================================================================
# Nirmana-Shell: PowerShell 7 Profile
# =====================================================================

# 1. Starship Prompt Engine
if (Get-Command starship -ErrorAction SilentlyContinue) {
    Invoke-Expression (&starship init powershell)
}

# 2. PSReadLine (Modern Autocomplete & Predictive IntelliSense)
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

    # - Ctrl+r: Interactive Fuzzy History Search via fzf (fullscreen layout matching zi)
    if (Get-Command fzf -ErrorAction SilentlyContinue) {
        Set-PSReadLineKeyHandler -Chord 'Ctrl+r' -ScriptBlock {
            $historyFile = (Get-PSReadLineOption).HistorySavePath
            if (Test-Path $historyFile) {
                $selected = Get-Content $historyFile -Encoding utf8 -ErrorAction SilentlyContinue |
                    fzf --tac --no-sort
                if ($selected) {
                    [Microsoft.PowerShell.PSConsoleReadLine]::RevertLine()
                    [Microsoft.PowerShell.PSConsoleReadLine]::Insert($selected)
                }
            }
        }
    }
}

# 3. Zoxide (Smarter 'cd' navigation via 'z')
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression (&zoxide init powershell | Out-String)
}

# 4. Eza (Modern 'ls' replacement with icons & colors)
if (Get-Command eza -ErrorAction SilentlyContinue) {
    if (Test-Path Alias:ls) { Remove-Item Alias:ls -Force }
    function ls { eza --icons --group-directories-first @args }
    function ll { eza --icons --group-directories-first -l @args }
    function la { eza --icons --group-directories-first -la @args }
    function lt { eza --icons --tree --level=2 @args }
}

# 5. Nirmana-Shell CLI Helper & Commands
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
                git -C $root pull
                & (Join-Path $root "setup.ps1")
            } else {
                Write-Host "Re-running Nirmana-Shell setup..." -ForegroundColor Cyan
                irm https://raw.githubusercontent.com/Andndre/nirmana-shell/main/setup.ps1 | iex
            }
        }
        'doctor' {
            Write-Host "`n=== Nirmana-Shell Health Check ===" -ForegroundColor Cyan
            $tools = @('pwsh', 'starship', 'zoxide', 'eza', 'fzf', 'delta', 'fd', 'rg')
            foreach ($t in $tools) {
                $found = Get-Command $t -ErrorAction SilentlyContinue
                if ($found) {
                    Write-Host " [+] $t -> $($found.Source)" -ForegroundColor Green
                } else {
                    Write-Host " [-] $t -> Not found in PATH" -ForegroundColor Red
                }
            }
            Write-Host ""
        }
        'reload' {
            . $PROFILE
            Write-Host "PowerShell 7 profile reloaded successfully." -ForegroundColor Green
        }
        default {
            Write-Host "Nirmana-Shell CLI" -ForegroundColor Cyan
            Write-Host "Usage: nirmana-shell <command> [arguments]`n" -ForegroundColor White
            Write-Host "Commands:" -ForegroundColor Yellow
            Write-Host "  theme [name]   Switch Starship theme interactively or directly"
            Write-Host "  update         Update Nirmana-Shell to the latest version from GitHub"
            Write-Host "  doctor         Check health of CLI dependencies (pwsh, starship, zoxide, etc.)"
            Write-Host "  reload         Reload `$PROFILE in this active session"
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
