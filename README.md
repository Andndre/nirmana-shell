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

---

## CLI Helper: `nirmana-shell`

The `nirmana-shell` command (alias: `nirmana`) is registered globally:

| Command | Description |
| :--- | :--- |
| `nirmana theme` | Open interactive theme switcher with top prompt preview and rounded borders |
| `nirmana theme <name>` | Apply a specific theme (supports Tab completion) |
| `nirmana doctor` | Verify PATH and health of all CLI tools |
| `nirmana update` | Pull latest updates from GitHub |
| `nirmana reload` | Reload the active PowerShell profile |

### Available Themes and Presets

Supports 17 custom themes and 10 official Starship presets. Preview images below are generated directly from the theme definitions.

<details open>
<summary><b>Custom Themes Gallery (17 Themes)</b></summary>

| Theme | Preview | Command |
| :--- | :--- | :--- |
| **nirmana**<br>_Signature cyan & purple_ | ![nirmana](assets/previews/nirmana.png) | `nirmana theme nirmana` |
| **catppuccin-mocha**<br>_Pastel aesthetic_ | ![catppuccin-mocha](assets/previews/catppuccin-mocha.png) | `nirmana theme catppuccin-mocha` |
| **takuya**<br>_Craftzdog capsule & clock_ | ![takuya](assets/previews/takuya.png) | `nirmana theme takuya` |
| **tokyo-night**<br>_Cyberpunk dark palette_ | ![tokyo-night](assets/previews/tokyo-night.png) | `nirmana theme tokyo-night` |
| **bubbles**<br>_Indigo capsules & vibrant accents_ | ![bubbles](assets/previews/bubbles.png) | `nirmana theme bubbles` |
| **powerlevel10k_rainbow**<br>_Multi-color rainbow ribbon_ | ![powerlevel10k_rainbow](assets/previews/powerlevel10k_rainbow.png) | `nirmana theme powerlevel10k_rainbow` |
| **minimal-emerald**<br>_Emerald green minimalist_ | ![minimal-emerald](assets/previews/minimal-emerald.png) | `nirmana theme minimal-emerald` |
| **clean-detailed**<br>_Right-aligned runtime & duration_ | ![clean-detailed](assets/previews/clean-detailed.png) | `nirmana theme clean-detailed` |
| **dracula**<br>_Official Dracula palette_ | ![dracula](assets/previews/dracula.png) | `nirmana theme dracula` |
| **spaceship**<br>_Cosmic developer prompt_ | ![spaceship](assets/previews/spaceship.png) | `nirmana theme spaceship` |
| **atomic**<br>_Warm orange & yellow pills_ | ![atomic](assets/previews/atomic.png) | `nirmana theme atomic` |
| **half-life**<br>_Electric green & orange lambda_ | ![half-life](assets/previews/half-life.png) | `nirmana theme half-life` |
| **paradox**<br>_Sky blue chevron segments_ | ![paradox](assets/previews/paradox.png) | `nirmana theme paradox` |
| **jandedobbeleer**<br>_Pink & yellow chevron prompt_ | ![jandedobbeleer](assets/previews/jandedobbeleer.png) | `nirmana theme jandedobbeleer` |
| **agnoster**<br>_Classic powerline ribbon_ | ![agnoster](assets/previews/agnoster.png) | `nirmana theme agnoster` |
| **jetpack**<br>_Futuristic geometric single-line_ | ![jetpack](assets/previews/jetpack.png) | `nirmana theme jetpack` |
| **robbyrussell**<br>_Legendary minimal arrow prompt_ | ![robbyrussell](assets/previews/robbyrussell.png) | `nirmana theme robbyrussell` |

</details>

<details>
<summary><b>Official Starship Presets (10 Presets)</b></summary>

| Preset | Preview | Command |
| :--- | :--- | :--- |
| **catppuccin-powerline** | ![catppuccin-powerline](assets/previews/catppuccin-powerline.png) | `nirmana theme catppuccin-powerline` |
| **gruvbox-rainbow** | ![gruvbox-rainbow](assets/previews/gruvbox-rainbow.png) | `nirmana theme gruvbox-rainbow` |
| **pastel-powerline** | ![pastel-powerline](assets/previews/pastel-powerline.png) | `nirmana theme pastel-powerline` |
| **bracketed-segments** | ![bracketed-segments](assets/previews/bracketed-segments.png) | `nirmana theme bracketed-segments` |
| **nerd-font-symbols** | ![nerd-font-symbols](assets/previews/nerd-font-symbols.png) | `nirmana theme nerd-font-symbols` |
| **no-empty-icons** | ![no-empty-icons](assets/previews/no-empty-icons.png) | `nirmana theme no-empty-icons` |
| **no-nerd-font** | ![no-nerd-font](assets/previews/no-nerd-font.png) | `nirmana theme no-nerd-font` |
| **no-runtime-versions** | ![no-runtime-versions](assets/previews/no-runtime-versions.png) | `nirmana theme no-runtime-versions` |
| **plain-text-symbols** | ![plain-text-symbols](assets/previews/plain-text-symbols.png) | `nirmana theme plain-text-symbols` |
| **pure-preset** | ![pure-preset](assets/previews/pure-preset.png) | `nirmana theme pure-preset` |

</details>

Usage example:
```powershell
nirmana theme
nirmana theme takuya
nirmana theme bubbles
nirmana theme robbyrussell
nirmana theme spaceship
nirmana theme catppuccin-mocha
```

---

## Repository Layout

```text
nirmana-shell/
├── LICENSE                 # MIT license and acknowledgements
├── README.md               # Documentation
├── setup.ps1               # Automated installer
├── switch-theme.ps1        # Theme switcher with real-time preview
├── preview.cmd             # Fast preview helper for FZF TUI
├── .previews/              # Pre-rendered theme preview cards (ANSI text)
├── assets/
│   └── previews/           # Pre-rendered PNG cards for documentation
├── configs/
│   └── Microsoft.PowerShell_profile.ps1 # PowerShell 7 profile
├── scripts/
│   └── generate-previews.py # Tool to render previews to PNG
└── themes/                 # 17 custom and adapted Starship themes (*.toml)
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
