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
