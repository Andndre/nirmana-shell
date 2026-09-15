# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.9] - 2026-09-16

### Added

- **Oh My Posh Transpiler (`scripts/convert-omp.py`)**: Built an automated transpiler engine that converts Oh My Posh JSON themes (`*.omp.json`) into high-performance Starship TOML themes, parsing segment metadata, colors, Go time formats to `strftime`, and multi-line layouts with right-aligned `$fill`.
- **Theme Importer CLI (`nirmana import-theme`)**: Added a first-class CLI command to import and transpile Oh My Posh themes directly from local files or remote GitHub URLs (`nirmana import-theme <url/file> [name]`), automatically generating preview cards and integrating them into the FZF theme switcher.
- **Curated Theme `1_shell`**: Ported the iconic `1_shell` pastel system information theme from Oh My Posh, featuring multi-line metrics (user, time, git, duration, memory usage) and clean directory styling.

## [1.0.8] - 2026-09-16

### Added

- **In-Session Profile Activation**: `setup.ps1` now automatically refreshes process `$env:Path` from registry (Machine and User) and dot-sources the newly installed profile into the active PowerShell 7 session, enabling immediate usage of the prompt and `nirmana` commands without requiring a terminal restart or new tab.
- **In-Session Uninstallation Purge**: `nirmana uninstall` now forcefully removes global aliases (`Remove-Alias -Scope Global`), unregisters functions, removes eza aliases, and restores the standard PowerShell prompt (or reloads the restored user profile) directly in the active session, preventing stale commands from remaining usable after uninstallation.

## [1.0.7] - 2026-09-16

### Fixed

- **Uninstallation Purge Completeness**: Hardened `nirmana uninstall` to inspect `.orig` and `.bak` backups for existing Nirmana profile signatures, preventing accidental self-restoration. Unregisters active in-memory aliases (`nirmana`) and functions from the running session, removes legacy PS 5.1 bridges, and deletes profiles cleanly if no pre-existing user profile existed.
- **Mid-Command F2 Prediction Toggle**: Updated F2 keyhandler to pass key context into native `[Microsoft.PowerShell.PSConsoleReadLine]::SwitchPredictionView($key, $arg)`, resolving UI render stalls when toggling between InlineView and ListView with text already present on the command line.
- **Benchmark TUI Box Alignment**: Fixed border width calculation and color bleeding in `nirmana benchmark`, ensuring borders are consistently rendered in cyan with aligned vertical lines across all rows.

## [1.0.6] - 2026-09-16

### Added

- **Self-Healing CLI (`nirmana doctor --fix`)**: Added `--fix` flag to automatically install missing CLI dependencies (`pwsh`, `starship`, `zoxide`, `eza`, `fzf`, `delta`, `fd`, `rg`) and Cascadia Code Nerd Font via WinGet.
- **Shell Startup Benchmark (`nirmana benchmark`)**: Added a profiling command that measures and displays sub-second latency across Starship initialization, PSReadLine configuration, Zoxide, settings deserialization, and user custom extensions.
- **Clean Uninstallation Suite (`nirmana uninstall`)**: Added an interactive rollback command to restore original PowerShell profiles from `.orig` backup and cleanly purge Nirmana runtime and configuration directories.
- **Automated Cascadia Code Nerd Font Provisioning**: Added `ryanoasis.CaskaydiaCove` from the `winget-font` source to `setup.ps1` with smart local font directory inspection.
- **Dedicated Dracula Terminal Color Scheme**: Added authentic Dracula palette (`#282A36` background) to Windows Terminal schemes injection and mapped it to the `dracula` theme.
- **Immutable Profile Preservation (`.orig`)**: `setup.ps1` now preserves pre-existing user profiles into `Microsoft.PowerShell_profile.ps1.orig` upon first run, ensuring pristine user configurations are never overwritten on subsequent updates.

### Fixed

- **Windows Terminal Scheme Clobbering**: Scoped Windows Terminal color scheme updates strictly to `profiles.defaults` in both `setup.ps1` and `switch-theme.ps1`, preventing unintentional mutation of independent profiles (WSL, Command Prompt).
- **Missing Ripgrep in Setup Toolchain**: Added `BurntSushi.ripgrep.MSVC` to WinGet installation list in `setup.ps1`, resolving `[-] rg Not found in PATH` in `nirmana doctor`.
- **PSReadLine Startup Latency**: Replaced disk-scanning `Get-Module -ListAvailable PSReadLine` with in-memory module validation, shaving 50-150ms from shell startup.
- **Profile Environment Leak**: Removed developer-specific Flutter Dart SDK path check (`$HOME\flutter\bin\cache\dart-sdk\bin`) from profile.
- **User Extension Error Boundary**: Wrapped user custom script (`custom.ps1`) execution in `try / catch` to isolate personal script syntax errors from breaking the core shell environment.

## [1.0.5] - 2026-09-15

### Added

- **F2 Prediction View Toggle Persistence**: Preference between PSReadLine `InlineView` and `ListView` is now automatically stored in `~/.config/nirmana/settings.json` upon pressing `F2` and restored across PowerShell sessions.
- **Active Theme Preservation during Update**: `setup.ps1` and `switch-theme.ps1` now persist and honor the active theme across updates (`nirmana update` / `setup.ps1`), preventing reset to the default theme.
- **User Customization Hook (`custom.ps1`)**: Introduced `~/.config/nirmana/custom.ps1` as an unmanaged user script loaded at profile end, allowing persistent custom aliases, environment variables, and functions across updates.
- **Zoxide `za` Shortcut**: Added `za` alias for `zoxide add` to quickly register directories to Zoxide database directly from the terminal prompt.
- **Automatic Zoxide Directory Seeding**: Automatically registers `$HOME`, `Downloads`, and `$installDir` on fresh installations when the Zoxide database is empty.
- **Windows Terminal Color Scheme Alignment**: Installer automatically aligns Windows Terminal color schemes to the active theme upon setup or update.

### Changed

- **Fallback Version String**: Updated default version fallback in `setup.ps1` to `1.0.5`.

## [1.0.4] - 2026-09-15

### Changed

- **Realistic Mock Project Context for Theme Previews**: Updated `Ensure-Previews` in `switch-theme.ps1` to render prompt previews within an isolated temporary mock project environment (`package.json`, `main.c`, and tracked git repository with dirty state). This activates language runtime badges, package details, and tooling modifiers across all custom themes and presets.
- **Differentiated Official Utility Presets**: Resolved identical output across official presets (`nerd-font-symbols`, `no-empty-icons`, `no-nerd-font`, `no-runtime-versions`) by providing active toolchain contexts where their formatting and filtering logic are visually demonstrable.
- **Extended Preview Console Width**: Increased Rich console rasterization width from 86 to 96 columns in `scripts/generate-previews.py` to prevent line wrapping on long single-line powerline ribbons with active runtimes.
- **Regenerated Preview Assets**: Updated all 27 `.previews/*.txt` ANSI cards and `assets/previews/*.png` preview cards.
- **Fallback Version String**: Updated default version fallback in `setup.ps1` to `1.0.4`.

## [1.0.3] - 2026-09-15

### Fixed

- **UTF-8 BOM Stripped from Setup Script**: Removed UTF-8 Byte Order Mark (`\uFEFF` / `EF BB BF`) from `setup.ps1` that caused `Invoke-Expression` pipeline execution (`irm ... | iex`) to fail with command-not-found errors on comment block headers (`The term '<#' is not recognized...`).
- **Comment Block Standardization**: Converted script headers to line comments (`#`) for resilience across varying PowerShell hosts and remote execution wrappers.
- **Fallback Version String**: Updated default version fallback in `setup.ps1` to `1.0.3`.

## [1.0.2] - 2026-09-15

### Added

- **Windows PowerShell 5.1 Compatibility**: Automatically detects execution from legacy PowerShell 5.1, installs PowerShell 7 via WinGet, sets it as the default profile in Windows Terminal, and provides dynamic next-step guidance.
- **Windows Terminal Default Profile Automation**: Automatically parses `settings.json` and updates `defaultProfile` to the PowerShell 7 profile GUID.
- **CRLF Line Ending Enforcement**: Added `.gitattributes` to ensure scripts retain Windows CRLF line endings, preventing parser errors in legacy PowerShell 5.1 here-strings.

## [1.0.1] - 2026-09-15

### Fixed

- Resolved null path binding error in `setup.ps1` when executed in-memory via `Invoke-Expression` pipeline (`irm ... | iex`).
- Hardened repository update mechanism in `setup.ps1` using `git fetch` and `git reset --hard` to avoid unstaged working tree conflicts.

## [1.0.0] - 2026-09-15

### Added

- **17 Custom and Adapted Themes**: Handcrafted Starship themes including `nirmana`, `catppuccin-mocha`, `takuya`, `tokyo-night`, `bubbles`, `minimal-emerald`, `clean-detailed`, `dracula`, `spaceship`, `atomic`, `half-life`, `paradox`, `jandedobbeleer`, `powerlevel10k_rainbow`, `agnoster`, `jetpack`, and `robbyrussell`.
- **Right-Aligned Layout**: Implemented Starship `$fill` module across all multi-line themes, moving language runtimes (Node.js, Python, Rust, Go, Dart, Bun) and command execution time to the right side of line 1.
- **Dynamic Theme Switcher**: Interactive FZF menu (`switch-theme.ps1` / `nirmana theme`) with real-time ANSI preview card, rounded borders, and Windows Terminal color scheme synchronization.
- **Pre-rendered Preview Generator**: Automated Python pipeline (`scripts/generate-previews.py`) utilizing Rich and resvg-py with `CaskaydiaCove NF` font mapping to produce pixel-perfect PNG cards for documentation.
- **Interactive Documentation Gallery**: Collapsible preview tables in README displaying rendered prompt visuals and direct activation commands for all 27 themes and presets.
- **CLI Management Suite**: Global `nirmana` helper supporting `theme`, `doctor`, `update`, `reload`, and `version`.
- **Automated Windows Setup**: `setup.ps1` installer configuring WinGet dependencies (`pwsh`, `git`, `starship`, `zoxide`, `eza`, `fzf`, `delta`, `fd`), Git delta pager, and PowerShell 7 profile.

### Fixed

- Prevented `$env:STARSHIP_CONFIG` temporary preview path leaks from corrupting active PowerShell sessions.
- Corrected Rich SVG font-family fallback to avoid Unicode Private Use Area (PUA) glyph mapping corruption.
- Adjusted rendering console width to 86 columns to eliminate false line-wrapping on single-line powerline ribbons.
