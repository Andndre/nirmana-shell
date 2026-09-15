# Nirmana-Shell

Automated modern terminal setup for Windows powered by **PowerShell 7**, **Starship**, **PSReadLine**, **Zoxide**, **Eza**, **FZF**, **Delta**, and **FD**.

---

## Quick Start (One-Command Install)

Open PowerShell (*Run as Administrator* recommended), then run:

### Option A: Online Installation (via GitHub)
```powershell
irm https://raw.githubusercontent.com/Andndre/nirmana-shell/main/setup.ps1 | iex
```

### Option B: Local Installation
If you have cloned or downloaded this repository directly:
```powershell
cd nirmana-shell
.\setup.ps1
```

The installer will automatically:
1. Install all modern CLI tools via WinGet (`pwsh`, `starship`, `zoxide`, `eza`, `fzf`, `delta`, `fd`).
2. Route Git Pager to `delta` for syntax-highlighted, word-level diffs.
3. Set up the local environment in `~/.nirmana-shell` and configure the PowerShell 7 profile.
4. Apply the signature Nirmana theme to Starship.
5. Silence the audio alert bell when backspacing at the beginning of a line.
6. Set PowerShell 7 as the default profile in Windows Terminal.

---

## Prerequisite: Nerd Font

All icons and glyphs in Starship and Eza require a **Nerd Font**.

1. Install Cascadia Code Nerd Font via WinGet:
   ```cmd
   winget install Microsoft.CascadiaCodeNF
   ```
2. In **Windows Terminal**: Go to **Settings (Ctrl + ,)** -> **Defaults** -> **Appearance** -> **Font face** -> Select **`CaskaydiaCove NF`**.

---

## Features & Keyboard Shortcuts

| Feature | Shortcut / Command | Description |
| :--- | :--- | :--- |
| **Inline Autocomplete** | Gray suggestion text | Fish-like command history predictions ahead of the cursor |
| **Accept Full Suggestion**| `→` (Right Arrow) / `End` | Accept the entire inline prediction |
| **Accept Word-by-Word** | `Ctrl + F` | Accept next word of prediction |
| **Toggle Suggestion View**| `F2` | Switch between *InlineView* (single-line) and *ListView* (dropdown) |
| **Interactive History** | `Ctrl + R` | Fullscreen fuzzy search of command history via `fzf` |
| **Menu Completion** | `Tab` | Interactive searchable completion grid for commands and paths |
| **Smart Directory Jump** | `z <folder>` | Jump to any visited folder across drives instantly |
| **Interactive Jump** | `zi` | Interactive directory selection menu via `fzf` |
| **Modern File Listing** | `ls`, `ll`, `la`, `lt` | Fast `eza` replacement with icons, colors, and permissions |
| **Enhanced Git Diff** | `git diff`, `git show` | Side-by-side or line-numbered syntax-highlighted diffs via `delta` |
| **Fast File Search** | `fd <filename>` | Blazing fast file finder (ignores `.git` & `node_modules` by default) |
| **Silent Backspace** | `Backspace` | Zero audio chime / bell beeps |

---

## `nirmana-shell` CLI Commands

Once installed, the `nirmana-shell` command (or shorthand alias `nirmana`) is globally available:

| Command | Description |
| :--- | :--- |
| `nirmana-shell theme` | Open interactive `fzf` menu to select and apply Starship themes |
| `nirmana-shell theme <name>` | Switch directly to a specific theme (supports **Tab autocomplete**) |
| `nirmana-shell doctor` | Check the health of all CLI tools (`pwsh`, `starship`, `zoxide`, `eza`, `fzf`, `delta`, `fd`, `rg`) |
| `nirmana-shell update` | Pull the latest changes and themes from GitHub |
| `nirmana-shell reload` | Reload the active PowerShell `$PROFILE` in the current session |

### Available Themes & Official Presets:

You can switch to any of Nirmana-Shell's custom-tuned themes or official Starship community presets (from [starship.rs/presets](https://starship.rs/presets/)):

* **Custom Tuned Themes**:
  * `nirmana` — Signature theme with vibrant cyan, amethyst accents, and clean contrast.
  * `catppuccin-mocha` — Soothing pastel aesthetic.
  * `tokyo-night` — Dark cyberpunk neon palette.
  * `minimal-emerald` — Distraction-free emerald green theme.
* **Official Starship Presets (Dynamic)**:
  * `bracketed-segments`, `catppuccin-powerline`, `gruvbox-rainbow`, `jetpack`, `nerd-font-symbols`, `no-empty-icons`, `no-nerd-font`, `no-runtime-versions`, `pastel-powerline`, `plain-text-symbols`, `pure-preset`, `tokyo-night`.

Example:
```powershell
nirmana theme gruvbox-rainbow
nirmana theme nirmana
```
*(Tip: Type `nirmana theme ` and press `Tab` to cycle through all available themes and presets).*

---

## Repository Structure

```text
nirmana-shell/
├── LICENSE                 # MIT License & third-party acknowledgements
├── README.md               # Documentation and usage guide
├── setup.ps1               # Automated one-command installer script
├── switch-theme.ps1        # Unified theme switcher script
├── configs/
│   └── Microsoft.PowerShell_profile.ps1 # Canonical PowerShell 7 profile
└── themes/
    ├── nirmana.toml
    ├── tokyo-night.toml
    ├── catppuccin-mocha.toml
    └── minimal-emerald.toml
```

---

## Sharing with Friends

Share this single command with anyone on Windows:

```powershell
irm https://raw.githubusercontent.com/Andndre/nirmana-shell/main/setup.ps1 | iex
```

---

## License & Legal Acknowledgements

Nirmana-Shell is open-source under the [MIT License](file:///D:/nirmana-shell/LICENSE).

It utilizes and integrates with the following open-source software under their respective licenses:
* [Starship](https://starship.rs) — Licensed under the **ISC License** (Copyright © 2019-present, Starship Contributors). Presets are rendered via Starship's official first-party `starship preset` mechanism.
* [Zoxide](https://github.com/ajeetdsouza/zoxide) — MIT License.
* [Eza](https://github.com/eza-community/eza) — EUPL-1.2 License.
* [FZF](https://github.com/junegunn/fzf) — MIT License.
* [Delta](https://github.com/dandavison/delta) — MIT License.
* [FD](https://github.com/sharkdp/fd) — MIT / Apache-2.0 License.
* [PSReadLine](https://github.com/PowerShell/PSReadLine) — MIT License.
