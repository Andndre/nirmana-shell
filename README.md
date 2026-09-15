# Nirmana-Shell

PowerShell 7 terminal environment for Windows. Configures Starship prompt, PSReadLine predictive completion, Zoxide directory navigation, Eza file listing, FZF history search, Delta git diffs, and FD.

---

## Quick Start

Open PowerShell as Administrator, then run:

### Remote Install
```powershell
irm https://raw.githubusercontent.com/Andndre/nirmana-shell/main/setup.ps1 | iex
```

### Local Install
```powershell
git clone https://github.com/Andndre/nirmana-shell.git
cd nirmana-shell
.\setup.ps1
```

The script performs the following tasks:
1. Installs required tools via WinGet (`pwsh`, `git`, `starship`, `zoxide`, `eza`, `fzf`, `delta`, `fd`).
2. Configures Git to use `delta` as the default pager.
3. Sets up `~/.nirmana-shell` and installs the PowerShell 7 profile.
4. Sets the default Starship configuration.
5. Disables the console bell on backspace.
6. Sets PowerShell 7 as the default profile in Windows Terminal.

---

## Prerequisite: Nerd Font

Icons used by Starship and Eza require a patched Nerd Font.

1. Install Cascadia Code Nerd Font via WinGet:
   ```cmd
   winget install Microsoft.CascadiaCodeNF
   ```
2. In Windows Terminal: Go to **Settings (Ctrl + ,)** > **Defaults** > **Appearance** > **Font face** > Select **`CaskaydiaCove NF`**.

---

## Shortcuts and Commands

| Feature | Shortcut / Command | Description |
| :--- | :--- | :--- |
| Inline Autocomplete | Gray text | History-based prediction |
| Accept Suggestion | `Right Arrow` / `End` | Accept full prediction |
| Accept Word | `Ctrl + F` | Accept next word of prediction |
| Toggle View | `F2` | Switch between inline and list prediction styles |
| History Search | `Ctrl + R` | Fullscreen fuzzy history search using `fzf` |
| Menu Completion | `Tab` | Interactive completion menu |
| Directory Jump | `z <folder>` | Jump to previously visited directory |
| Interactive Jump | `zi` | Select directory interactively via `fzf` |
| File Listing | `ls`, `ll`, `la`, `lt` | Directory listing using `eza` |
| Git Diffs | `git diff`, `git show` | Syntax-highlighted diffs using `delta` |
| File Search | `fd <query>` | Fast file search |
| Console Bell | `Backspace` | Muted; no audio beep |

---

## CLI Helper: `nirmana-shell`

The `nirmana-shell` command (alias: `nirmana`) is registered globally:

| Command | Description |
| :--- | :--- |
| `nirmana theme` | Open interactive `fzf` picker to switch themes |
| `nirmana theme <name>` | Apply a specific theme (supports Tab completion) |
| `nirmana doctor` | Verify PATH and health of all CLI tools |
| `nirmana update` | Pull latest updates from GitHub |
| `nirmana reload` | Reload the active PowerShell profile |

### Available Themes and Presets

Supports custom presets and official Starship presets:

* **Custom Presets**:
  * `nirmana`: Default theme with cyan and purple accents
  * `catppuccin-mocha`: Catppuccin Mocha palette
  * `tokyo-night`: Tokyo Night palette
  * `minimal-emerald`: Emerald green accent theme
* **Official Starship Presets**:
  * `bracketed-segments`, `catppuccin-powerline`, `gruvbox-rainbow`, `jetpack`, `nerd-font-symbols`, `no-empty-icons`, `no-nerd-font`, `no-runtime-versions`, `pastel-powerline`, `plain-text-symbols`, `pure-preset`, `tokyo-night`

Usage example:
```powershell
nirmana theme gruvbox-rainbow
nirmana theme nirmana
```

---

## Repository Layout

```text
nirmana-shell/
├── LICENSE                 # MIT license and acknowledgements
├── README.md               # Documentation
├── setup.ps1               # Automated installer
├── switch-theme.ps1        # Theme switcher
├── configs/
│   └── Microsoft.PowerShell_profile.ps1 # PowerShell 7 profile
└── themes/
    ├── nirmana.toml
    ├── tokyo-night.toml
    ├── catppuccin-mocha.toml
    └── minimal-emerald.toml
```

---

## License

MIT License. See [LICENSE](file:///D:/nirmana-shell/LICENSE) for details.

Includes integrations with:
* Starship (ISC License): https://starship.rs
* Zoxide (MIT License): https://github.com/ajeetdsouza/zoxide
* Eza (EUPL-1.2 License): https://github.com/eza-community/eza
* FZF (MIT License): https://github.com/junegunn/fzf
* Delta (MIT License): https://github.com/dandavison/delta
* FD (MIT/Apache-2.0 License): https://github.com/sharkdp/fd
* PSReadLine (MIT License): https://github.com/PowerShell/PSReadLine
