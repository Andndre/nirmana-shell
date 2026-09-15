# =====================================================================
# Tridatu-Shell — PowerShell 7 Profile
# =====================================================================

# 1. Starship Prompt Engine
if (Get-Command starship -ErrorAction SilentlyContinue) {
    Invoke-Expression (&starship init powershell)
}

# 2. PSReadLine (Modern Autocomplete & Predictive IntelliSense)
if (Get-Module -ListAvailable PSReadLine) {
    Import-Module PSReadLine

    # Matikan suara beep / bell audio saat menekan backspace di baris kosong
    Set-PSReadLineOption -BellStyle None

    # Prediksi inline hanya aktif jika berada di terminal interaktif (VT-supported)
    if (-not [System.Console]::IsOutputRedirected) {
        Set-PSReadLineOption -PredictionSource History -ErrorAction SilentlyContinue
        Set-PSReadLineOption -PredictionViewStyle InlineView -ErrorAction SilentlyContinue
        Set-PSReadLineOption -Colors @{ InlinePrediction = '#767676' } -ErrorAction SilentlyContinue
    }

    # Key Handlers:
    # - Tab: Menu completion grid interaktif
    Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete

    # - Ctrl+f: Terima prediksi per kata (Fish style)
    Set-PSReadLineKeyHandler -Chord 'Ctrl+f' -Function ForwardWord

    # - Ctrl+r: Interactive Fuzzy History Search via fzf (tampilan identik dengan zi)
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

# 5. Tridatu-Shell CLI Helper & Commands
function global:tridatu-shell {
    param(
        [Parameter(Position=0)]
        [string]$SubCommand,
        [Parameter(Position=1)]
        [string]$Argument
    )

    $root = Join-Path $HOME ".tridatu-shell"
    switch ($SubCommand) {
        'theme' {
            $switchScript = Join-Path $root "switch-theme.ps1"
            if (Test-Path $switchScript) {
                & $switchScript $Argument
            } else {
                Write-Error "Skrip tema tidak ditemukan di $root"
            }
        }
        'update' {
            if (Test-Path (Join-Path $root ".git")) {
                Write-Host "Memperbarui Tridatu-Shell dari GitHub..." -ForegroundColor Cyan
                git -C $root pull
                & (Join-Path $root "setup.ps1")
            } else {
                Write-Host "Mengunduh ulang setup Tridatu-Shell..." -ForegroundColor Cyan
                irm https://raw.githubusercontent.com/Andndre/tridatu-shell/main/setup.ps1 | iex
            }
        }
        'doctor' {
            Write-Host "`n=== Pemeriksaan Kesehatan Tridatu-Shell ===" -ForegroundColor Cyan
            $tools = @('pwsh', 'starship', 'zoxide', 'eza', 'fzf', 'delta', 'fd', 'rg')
            foreach ($t in $tools) {
                $found = Get-Command $t -ErrorAction SilentlyContinue
                if ($found) {
                    Write-Host " [✓] $t -> $($found.Source)" -ForegroundColor Green
                } else {
                    Write-Host " [✗] $t -> Tidak ditemukan di PATH" -ForegroundColor Red
                }
            }
            Write-Host ""
        }
        'reload' {
            . $PROFILE
            Write-Host "Profil PowerShell 7 berhasil dimuat ulang." -ForegroundColor Green
        }
        default {
            Write-Host "Tridatu-Shell CLI" -ForegroundColor Red
            Write-Host "Penggunaan: tridatu-shell <perintah> [argumen]`n" -ForegroundColor White
            Write-Host "Perintah:" -ForegroundColor Yellow
            Write-Host "  theme [nama]   Ganti tema Starship secara interaktif atau langsung"
            Write-Host "  update         Perbarui tridatu-shell ke versi terbaru dari GitHub"
            Write-Host "  doctor         Periksa status dependensi CLI (pwsh, starship, zoxide, dll.)"
            Write-Host "  reload         Muat ulang `$PROFILE sesi aktif ini"
        }
    }
}
Set-Alias -Name tridatu -Value tridatu-shell -Option AllScope -Scope Global -Force

# Autocomplete untuk perintah tridatu-shell
Register-ArgumentCompleter -Native -CommandName 'tridatu-shell', 'tridatu' -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    $subcommands = @('theme', 'update', 'doctor', 'reload')
    $elements = $commandAst.CommandElements
    if ($elements.Count -eq 2) {
        $subcommands | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
        }
    } elseif ($elements.Count -eq 3 -and $elements[1].Value -eq 'theme') {
        $root = Join-Path $HOME ".tridatu-shell"
        if (Test-Path (Join-Path $root "themes")) {
            Get-ChildItem (Join-Path $root "themes") -Filter "*.toml" | ForEach-Object {
                $themeName = $_.BaseName
                if ($themeName -like "$wordToComplete*") {
                    [System.Management.Automation.CompletionResult]::new($themeName, $themeName, 'ParameterValue', $themeName)
                }
            }
        }
    }
}
