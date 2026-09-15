# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
