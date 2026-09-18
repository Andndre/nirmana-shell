# Nirmana-Shell

PowerShell 7 terminal environment for Windows. Configures Starship prompt, PSReadLine predictive completion, Zoxide directory navigation, Eza file listing, FZF history search, Delta git diffs, FD, and Ripgrep.

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

1. Installs required tools via WinGet (`pwsh`, `git`, `starship`, `zoxide`, `eza`, `fzf`, `delta`, `fd`, `rg`, and Cascadia Code Nerd Font).
2. Configures Git to use `delta` as the default pager.
3. Sets up `~/.nirmana-shell` and installs the PowerShell 7 profile (preserving pre-existing profiles in `.orig`).
4. Sets the default Starship configuration.
5. Disables the console bell on backspace.
6. Sets PowerShell 7 as the default profile in Windows Terminal with synchronized color schemes.

---

## Font Configuration: Nerd Font

Icons used by Starship and Eza require a patched Nerd Font. `setup.ps1` automatically installs Cascadia Code Nerd Font via WinGet.

If configuring manually or verifying:

1. Ensure Cascadia Code Nerd Font is installed (or run `nirmana doctor --fix`).
2. In Windows Terminal: Go to **Settings (Ctrl + ,)** > **Defaults** > **Appearance** > **Font face** > Select **`CaskaydiaCove NF`**.

---

## Shortcuts and Commands

| Feature             | Shortcut / Command     | Description                                                           |
| :------------------ | :--------------------- | :-------------------------------------------------------------------- |
| Inline Autocomplete | Gray text              | History-based prediction                                              |
| Accept Suggestion   | `Right Arrow` / `End`  | Accept full prediction                                                |
| Accept Word         | `Ctrl + F`             | Accept next word of prediction                                        |
| Toggle View         | `F2`                   | Switch between inline and list prediction (persisted across sessions) |
| History Search      | `Ctrl + R`             | Fullscreen fuzzy history search using `fzf`                           |
| Menu Completion     | `Tab`                  | Interactive completion menu                                           |
| Directory Jump      | `z <folder>`           | Jump to previously visited directory                                  |
| Interactive Jump    | `zi`                   | Select directory interactively via `fzf`                              |
| Add Directory       | `za [folder]`          | Add directory to zoxide (default: current folder)                     |
| File Listing        | `ls`, `ll`, `la`, `lt` | Directory listing using `eza`                                         |
| Git Diffs           | `git diff`, `git show` | Syntax-highlighted diffs using `delta`                                |
| File Search         | `fd <query>`           | Fast file search                                                      |
| Text Search         | `rg <query>`           | Fast recursive regex text search                                      |

> [!TIP]
> **User Custom Extensions:** Place personal functions, tokens, and aliases in `~/.config/nirmana/custom.ps1`. This file is loaded automatically by your profile and is **never overwritten** during Nirmana-Shell updates.
> **Persistent Preferences:** Theme choice and F2 prediction view style are saved in `~/.config/nirmana/settings.json` and survive all updates.

---

## CLI Helper: `nirmana-shell`

The `nirmana-shell` command (alias: `nirmana`) is registered globally:

| Command                                  | Description                                                                 |
| :--------------------------------------- | :-------------------------------------------------------------------------- |
| `nirmana theme`                          | Open interactive theme switcher with top prompt preview and rounded borders |
| `nirmana theme <name>`                   | Apply a specific theme (supports Tab completion)                            |
| `nirmana import-theme <url/file> [name]` | Import & transpile Oh My Posh theme JSON to Starship TOML                   |
| `nirmana version`                        | Display installed version, commit hash, and PowerShell environment          |
| `nirmana doctor`                         | Verify PATH and health of all CLI tools and Nerd Font status                |
| `nirmana doctor --fix`                   | Automatically install missing CLI dependencies and fonts via WinGet         |
| `nirmana benchmark`                      | Profile sub-second startup latency across profile components                |
| `nirmana update`                         | Pull latest updates from GitHub                                             |
| `nirmana reload`                         | Reload the active PowerShell profile                                        |
| `nirmana uninstall`                      | Interactively remove Nirmana and restore original profile backup            |

### Available Themes and Presets

Supports 17 curated custom themes, 109 ported Oh My Posh community themes, and 10 official Starship presets (total: 136 themes). All themes are fully integrated with the interactive FZF switcher (`nirmana theme`).

<details open>
<summary><b>Custom Themes Gallery (18 Curated Themes)</b></summary>

| Theme                                                     | Preview                                                             | Command                               |
| :-------------------------------------------------------- | :------------------------------------------------------------------ | :------------------------------------ |
| **nirmana**<br>_Signature cyan & purple_                  | ![nirmana](assets/previews/nirmana.png)                             | `nirmana theme nirmana`               |
| **catppuccin-mocha**<br>_Pastel aesthetic_                | ![catppuccin-mocha](assets/previews/catppuccin-mocha.png)           | `nirmana theme catppuccin-mocha`      |
| **takuya**<br>_Craftzdog capsule & clock_                 | ![takuya](assets/previews/takuya.png)                               | `nirmana theme takuya`                |
| **tokyo-night**<br>_Cyberpunk dark palette_               | ![tokyo-night](assets/previews/tokyo-night.png)                     | `nirmana theme tokyo-night`           |
| **bubbles**<br>_Indigo capsules & vibrant accents_        | ![bubbles](assets/previews/bubbles.png)                             | `nirmana theme bubbles`               |
| **powerlevel10k_rainbow**<br>_Multi-color rainbow ribbon_ | ![powerlevel10k_rainbow](assets/previews/powerlevel10k_rainbow.png) | `nirmana theme powerlevel10k_rainbow` |
| **minimal-emerald**<br>_Emerald green minimalist_         | ![minimal-emerald](assets/previews/minimal-emerald.png)             | `nirmana theme minimal-emerald`       |
| **clean-detailed**<br>_Right-aligned runtime & duration_  | ![clean-detailed](assets/previews/clean-detailed.png)               | `nirmana theme clean-detailed`        |
| **dracula**<br>_Official Dracula palette_                 | ![dracula](assets/previews/dracula.png)                             | `nirmana theme dracula`               |
| **spaceship**<br>_Cosmic developer prompt_                | ![spaceship](assets/previews/spaceship.png)                         | `nirmana theme spaceship`             |
| **atomic**<br>_Warm orange & yellow pills_                | ![atomic](assets/previews/atomic.png)                               | `nirmana theme atomic`                |
| **half-life**<br>_Electric green & orange lambda_         | ![half-life](assets/previews/half-life.png)                         | `nirmana theme half-life`             |
| **paradox**<br>_Sky blue chevron segments_                | ![paradox](assets/previews/paradox.png)                             | `nirmana theme paradox`               |
| **jandedobbeleer**<br>_Pink & yellow chevron prompt_      | ![jandedobbeleer](assets/previews/jandedobbeleer.png)               | `nirmana theme jandedobbeleer`        |
| **agnoster**<br>_Classic powerline ribbon_                | ![agnoster](assets/previews/agnoster.png)                           | `nirmana theme agnoster`              |
| **jetpack**<br>_Futuristic geometric single-line_         | ![jetpack](assets/previews/jetpack.png)                             | `nirmana theme jetpack`               |
| **robbyrussell**<br>_Legendary minimal arrow prompt_      | ![robbyrussell](assets/previews/robbyrussell.png)                   | `nirmana theme robbyrussell`          |
| **1_shell**<br>_Pastel system info prompt (OMP)_          | ![1_shell](assets/previews/1_shell.png)                             | `nirmana theme 1_shell`               |

</details>

<details>
<summary><b>Ported Oh My Posh Themes (109 Themes - Click to Expand)</b></summary>

| Theme | Preview | Command |
| :---- | :------ | :------ |
| **agnoster.minimal** | ![agnoster.minimal](assets/previews/agnoster.minimal.png) | `nirmana theme agnoster.minimal` |
| **agnosterplus** | ![agnosterplus](assets/previews/agnosterplus.png) | `nirmana theme agnosterplus` |
| **aliens** | ![aliens](assets/previews/aliens.png) | `nirmana theme aliens` |
| **amro** | ![amro](assets/previews/amro.png) | `nirmana theme amro` |
| **atomicBit** | ![atomicBit](assets/previews/atomicBit.png) | `nirmana theme atomicBit` |
| **avit** | ![avit](assets/previews/avit.png) | `nirmana theme avit` |
| **blue-owl** | ![blue-owl](assets/previews/blue-owl.png) | `nirmana theme blue-owl` |
| **blueish** | ![blueish](assets/previews/blueish.png) | `nirmana theme blueish` |
| **bubblesextra** | ![bubblesextra](assets/previews/bubblesextra.png) | `nirmana theme bubblesextra` |
| **bubblesline** | ![bubblesline](assets/previews/bubblesline.png) | `nirmana theme bubblesline` |
| **capr4n** | ![capr4n](assets/previews/capr4n.png) | `nirmana theme capr4n` |
| **catppuccin** | ![catppuccin](assets/previews/catppuccin.png) | `nirmana theme catppuccin` |
| **catppuccin_frappe** | ![catppuccin_frappe](assets/previews/catppuccin_frappe.png) | `nirmana theme catppuccin_frappe` |
| **catppuccin_latte** | ![catppuccin_latte](assets/previews/catppuccin_latte.png) | `nirmana theme catppuccin_latte` |
| **catppuccin_macchiato** | ![catppuccin_macchiato](assets/previews/catppuccin_macchiato.png) | `nirmana theme catppuccin_macchiato` |
| **cert** | ![cert](assets/previews/cert.png) | `nirmana theme cert` |
| **chips** | ![chips](assets/previews/chips.png) | `nirmana theme chips` |
| **cinnamon** | ![cinnamon](assets/previews/cinnamon.png) | `nirmana theme cinnamon` |
| **cloud-context** | ![cloud-context](assets/previews/cloud-context.png) | `nirmana theme cloud-context` |
| **cloud-native-azure** | ![cloud-native-azure](assets/previews/cloud-native-azure.png) | `nirmana theme cloud-native-azure` |
| **cobalt2** | ![cobalt2](assets/previews/cobalt2.png) | `nirmana theme cobalt2` |
| **craver** | ![craver](assets/previews/craver.png) | `nirmana theme craver` |
| **darkblood** | ![darkblood](assets/previews/darkblood.png) | `nirmana theme darkblood` |
| **di4am0nd** | ![di4am0nd](assets/previews/di4am0nd.png) | `nirmana theme di4am0nd` |
| **easy-term** | ![easy-term](assets/previews/easy-term.png) | `nirmana theme easy-term` |
| **emodipt** | ![emodipt](assets/previews/emodipt.png) | `nirmana theme emodipt` |
| **emodipt-extend** | ![emodipt-extend](assets/previews/emodipt-extend.png) | `nirmana theme emodipt-extend` |
| **fish** | ![fish](assets/previews/fish.png) | `nirmana theme fish` |
| **free-ukraine** | ![free-ukraine](assets/previews/free-ukraine.png) | `nirmana theme free-ukraine` |
| **froczh** | ![froczh](assets/previews/froczh.png) | `nirmana theme froczh` |
| **gmay** | ![gmay](assets/previews/gmay.png) | `nirmana theme gmay` |
| **grandpa-style** | ![grandpa-style](assets/previews/grandpa-style.png) | `nirmana theme grandpa-style` |
| **gruvbox** | ![gruvbox](assets/previews/gruvbox.png) | `nirmana theme gruvbox` |
| **honukai** | ![honukai](assets/previews/honukai.png) | `nirmana theme honukai` |
| **hotstick.minimal** | ![hotstick.minimal](assets/previews/hotstick.minimal.png) | `nirmana theme hotstick.minimal` |
| **hul10** | ![hul10](assets/previews/hul10.png) | `nirmana theme hul10` |
| **hunk** | ![hunk](assets/previews/hunk.png) | `nirmana theme hunk` |
| **huvix** | ![huvix](assets/previews/huvix.png) | `nirmana theme huvix` |
| **if_tea** | ![if_tea](assets/previews/if_tea.png) | `nirmana theme if_tea` |
| **illusi0n** | ![illusi0n](assets/previews/illusi0n.png) | `nirmana theme illusi0n` |
| **iterm2** | ![iterm2](assets/previews/iterm2.png) | `nirmana theme iterm2` |
| **jandedobbeleer-accessible** | ![jandedobbeleer-accessible](assets/previews/jandedobbeleer-accessible.png) | `nirmana theme jandedobbeleer-accessible` |
| **jblab_2021** | ![jblab_2021](assets/previews/jblab_2021.png) | `nirmana theme jblab_2021` |
| **jonnychipz** | ![jonnychipz](assets/previews/jonnychipz.png) | `nirmana theme jonnychipz` |
| **json** | ![json](assets/previews/json.png) | `nirmana theme json` |
| **jtracey93** | ![jtracey93](assets/previews/jtracey93.png) | `nirmana theme jtracey93` |
| **jv_sitecorian** | ![jv_sitecorian](assets/previews/jv_sitecorian.png) | `nirmana theme jv_sitecorian` |
| **kali** | ![kali](assets/previews/kali.png) | `nirmana theme kali` |
| **kushal** | ![kushal](assets/previews/kushal.png) | `nirmana theme kushal` |
| **lambda** | ![lambda](assets/previews/lambda.png) | `nirmana theme lambda` |
| **lambdageneration** | ![lambdageneration](assets/previews/lambdageneration.png) | `nirmana theme lambdageneration` |
| **larserikfinholt** | ![larserikfinholt](assets/previews/larserikfinholt.png) | `nirmana theme larserikfinholt` |
| **lightgreen** | ![lightgreen](assets/previews/lightgreen.png) | `nirmana theme lightgreen` |
| **M365Princess** | ![M365Princess](assets/previews/M365Princess.png) | `nirmana theme M365Princess` |
| **marcduiker** | ![marcduiker](assets/previews/marcduiker.png) | `nirmana theme marcduiker` |
| **markbull** | ![markbull](assets/previews/markbull.png) | `nirmana theme markbull` |
| **material** | ![material](assets/previews/material.png) | `nirmana theme material` |
| **microverse-power** | ![microverse-power](assets/previews/microverse-power.png) | `nirmana theme microverse-power` |
| **mojada** | ![mojada](assets/previews/mojada.png) | `nirmana theme mojada` |
| **montys** | ![montys](assets/previews/montys.png) | `nirmana theme montys` |
| **mt** | ![mt](assets/previews/mt.png) | `nirmana theme mt` |
| **multiverse-neon** | ![multiverse-neon](assets/previews/multiverse-neon.png) | `nirmana theme multiverse-neon` |
| **negligible** | ![negligible](assets/previews/negligible.png) | `nirmana theme negligible` |
| **neko** | ![neko](assets/previews/neko.png) | `nirmana theme neko` |
| **night-owl** | ![night-owl](assets/previews/night-owl.png) | `nirmana theme night-owl` |
| **nordtron** | ![nordtron](assets/previews/nordtron.png) | `nirmana theme nordtron` |
| **nu4a** | ![nu4a](assets/previews/nu4a.png) | `nirmana theme nu4a` |
| **onehalf.minimal** | ![onehalf.minimal](assets/previews/onehalf.minimal.png) | `nirmana theme onehalf.minimal` |
| **pararussel** | ![pararussel](assets/previews/pararussel.png) | `nirmana theme pararussel` |
| **patriksvensson** | ![patriksvensson](assets/previews/patriksvensson.png) | `nirmana theme patriksvensson` |
| **peru** | ![peru](assets/previews/peru.png) | `nirmana theme peru` |
| **pixelrobots** | ![pixelrobots](assets/previews/pixelrobots.png) | `nirmana theme pixelrobots` |
| **plague** | ![plague](assets/previews/plague.png) | `nirmana theme plague` |
| **poshmon** | ![poshmon](assets/previews/poshmon.png) | `nirmana theme poshmon` |
| **powerlevel10k_classic** | ![powerlevel10k_classic](assets/previews/powerlevel10k_classic.png) | `nirmana theme powerlevel10k_classic` |
| **powerlevel10k_lean** | ![powerlevel10k_lean](assets/previews/powerlevel10k_lean.png) | `nirmana theme powerlevel10k_lean` |
| **powerlevel10k_modern** | ![powerlevel10k_modern](assets/previews/powerlevel10k_modern.png) | `nirmana theme powerlevel10k_modern` |
| **powerline** | ![powerline](assets/previews/powerline.png) | `nirmana theme powerline` |
| **probua.minimal** | ![probua.minimal](assets/previews/probua.minimal.png) | `nirmana theme probua.minimal` |
| **pure** | ![pure](assets/previews/pure.png) | `nirmana theme pure` |
| **quick-term** | ![quick-term](assets/previews/quick-term.png) | `nirmana theme quick-term` |
| **remk** | ![remk](assets/previews/remk.png) | `nirmana theme remk` |
| **rudolfs-dark** | ![rudolfs-dark](assets/previews/rudolfs-dark.png) | `nirmana theme rudolfs-dark` |
| **rudolfs-light** | ![rudolfs-light](assets/previews/rudolfs-light.png) | `nirmana theme rudolfs-light` |
| **sim-web** | ![sim-web](assets/previews/sim-web.png) | `nirmana theme sim-web` |
| **slim** | ![slim](assets/previews/slim.png) | `nirmana theme slim` |
| **slimfat** | ![slimfat](assets/previews/slimfat.png) | `nirmana theme slimfat` |
| **smoothie** | ![smoothie](assets/previews/smoothie.png) | `nirmana theme smoothie` |
| **sonicboom_dark** | ![sonicboom_dark](assets/previews/sonicboom_dark.png) | `nirmana theme sonicboom_dark` |
| **sonicboom_light** | ![sonicboom_light](assets/previews/sonicboom_light.png) | `nirmana theme sonicboom_light` |
| **sorin** | ![sorin](assets/previews/sorin.png) | `nirmana theme sorin` |
| **space** | ![space](assets/previews/space.png) | `nirmana theme space` |
| **star** | ![star](assets/previews/star.png) | `nirmana theme star` |
| **stelbent-compact.minimal** | ![stelbent-compact.minimal](assets/previews/stelbent-compact.minimal.png) | `nirmana theme stelbent-compact.minimal` |
| **stelbent.minimal** | ![stelbent.minimal](assets/previews/stelbent.minimal.png) | `nirmana theme stelbent.minimal` |
| **the-unnamed** | ![the-unnamed](assets/previews/the-unnamed.png) | `nirmana theme the-unnamed` |
| **thecyberden** | ![thecyberden](assets/previews/thecyberden.png) | `nirmana theme thecyberden` |
| **tiwahu** | ![tiwahu](assets/previews/tiwahu.png) | `nirmana theme tiwahu` |
| **tokyo** | ![tokyo](assets/previews/tokyo.png) | `nirmana theme tokyo` |
| **tonybaloney** | ![tonybaloney](assets/previews/tonybaloney.png) | `nirmana theme tonybaloney` |
| **uew** | ![uew](assets/previews/uew.png) | `nirmana theme uew` |
| **unicorn** | ![unicorn](assets/previews/unicorn.png) | `nirmana theme unicorn` |
| **velvet** | ![velvet](assets/previews/velvet.png) | `nirmana theme velvet` |
| **wholespace** | ![wholespace](assets/previews/wholespace.png) | `nirmana theme wholespace` |
| **wopian** | ![wopian](assets/previews/wopian.png) | `nirmana theme wopian` |
| **xtoys** | ![xtoys](assets/previews/xtoys.png) | `nirmana theme xtoys` |
| **ys** | ![ys](assets/previews/ys.png) | `nirmana theme ys` |
| **zash** | ![zash](assets/previews/zash.png) | `nirmana theme zash` |

</details>

<details open>
<summary><b>Official Starship Presets (10 Presets)</b></summary>

| Preset                   | Preview                                                           | Command                              |
| :----------------------- | :---------------------------------------------------------------- | :----------------------------------- |
| **catppuccin-powerline** | ![catppuccin-powerline](assets/previews/catppuccin-powerline.png) | `nirmana theme catppuccin-powerline` |
| **gruvbox-rainbow**      | ![gruvbox-rainbow](assets/previews/gruvbox-rainbow.png)           | `nirmana theme gruvbox-rainbow`      |
| **pastel-powerline**     | ![pastel-powerline](assets/previews/pastel-powerline.png)         | `nirmana theme pastel-powerline`     |
| **bracketed-segments**   | ![bracketed-segments](assets/previews/bracketed-segments.png)     | `nirmana theme bracketed-segments`   |
| **nerd-font-symbols**    | ![nerd-font-symbols](assets/previews/nerd-font-symbols.png)       | `nirmana theme nerd-font-symbols`    |
| **no-empty-icons**       | ![no-empty-icons](assets/previews/no-empty-icons.png)             | `nirmana theme no-empty-icons`       |
| **no-nerd-font**         | ![no-nerd-font](assets/previews/no-nerd-font.png)                 | `nirmana theme no-nerd-font`         |
| **no-runtime-versions**  | ![no-runtime-versions](assets/previews/no-runtime-versions.png)   | `nirmana theme no-runtime-versions`  |
| **plain-text-symbols**   | ![plain-text-symbols](assets/previews/plain-text-symbols.png)     | `nirmana theme plain-text-symbols`   |
| **pure-preset**          | ![pure-preset](assets/previews/pure-preset.png)                   | `nirmana theme pure-preset`          |

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

## Oh My Posh Theme Transpiler (`nirmana import-theme`)

Nirmana-Shell includes a built-in transpiler engine ([convert-omp.py](scripts/convert-omp.py)) that translates Oh My Posh JSON themes (`*.omp.json`) into native, high-performance Starship configurations (`*.toml`).

### Key Capabilities

- **Zero Runtime Overhead:** Enjoy community theme aesthetics on Starship's compiled Rust engine (<10ms latency), eliminating the 50ms - 150ms shell startup latency of Go-based prompt engines on Windows.
- **Layout Normalization:** Adapts arbitrary block sequences into Nirmana's standard multi-line architecture with dynamic `$fill` right-alignment for execution duration and hardware metrics.
- **Color & Powerline Preservation:** Accurately maps hex palettes, palette lookups (`p:color`), diamond capsules (``/``), and powerline chevrons (``/``).
- **Automated Visual Previews:** Automatically generates both ANSI TUI preview cards (`.previews/`) and high-resolution rasterized PNG cards (`assets/previews/`) upon import.

### How to Import

Import any Oh My Posh theme using the `nirmana import-theme` command:

```powershell
# 1. Import by shorthand name directly from the official Oh My Posh repository
nirmana import-theme quick-term

# 2. Import from a custom remote URL (e.g. GitHub raw) with an optional custom name
nirmana import-theme https://raw.githubusercontent.com/.../custom.omp.json my-theme

# 3. Import from a local file
nirmana import-theme .\my-theme.omp.json
```

Alternatively, run the transpiler script directly via `uv`:

```powershell
uv run python scripts/convert-omp.py quick-term --output themes/quick-term.toml
```

Regenerate the maintained Oh My Posh collection directly from the upstream repository. This rewrites only the themes listed in [`scripts/omp-themes.txt`](scripts/omp-themes.txt); curated Nirmana themes remain unchanged.

```powershell
uv run --with rich --with resvg-py python scripts/convert-omp.py --upstream --output themes
```

---

## Why Starship?

Nirmana-Shell selects [Starship](https://starship.rs) as its core prompt engine for distinct architectural advantages:

- **High Performance (Rust-Native):** Starship is compiled to native machine code with zero runtime overhead. Prompt latency consistently remains under 10ms, eliminating terminal input stutter even in large repositories and complex directories.
- **Universal Portability:** A single `starship.toml` configuration file works identically across PowerShell 7, Bash, Zsh, Fish, and NuShell on Windows, Linux, and macOS.
- **Declarative Configuration:** Uses clean TOML syntax instead of complex shell script evaluation or deeply nested JSON/YAML structures.
- **Intelligent Module Caching:** Modules for Git status, language runtimes, and command durations execute asynchronously and cache results, preventing terminal freezes during network or slow disk operations.

---

## Comparison with Alternatives

How Nirmana-Shell compares against other popular Windows terminal configurations and prompt tools:

| Feature / Aspect              | Nirmana-Shell                                    | Chris Titus Tech (`win-dotfiles`) | Oh My Posh (`oh-my-posh`)  | Standalone Dotfiles        |
| :---------------------------- | :----------------------------------------------- | :-------------------------------- | :------------------------- | :------------------------- |
| **Prompt Engine**             | Starship (Rust)                                  | Starship (Rust)                   | Oh My Posh (Go)            | Varies (Starship / Custom) |
| **Primary Scope**             | Full Terminal Environment & Theme Suite          | Windows Tweaks & General Dotfiles | Prompt Engine Only         | Personal Configs           |
| **Installation**              | 1-Line Remote (`irm ... \| iex`)                 | PowerShell / Batch Script         | Package Manager (`winget`) | Manual Git Clone & Copy    |
| **Curated Themes**            | 18 Curated + 108 OMP + 10 Presets                | 1 Default Theme                   | 100+ Community Themes      | 1 Custom Theme             |
| **Interactive TUI Switcher**  | Built-in (`nirmana theme` via FZF)               | None (Static Config)              | CLI / Manual Config        | None                       |
| **Terminal Scheme Sync**      | Automatic (Windows Terminal JSON)                | Partial                           | Manual                     | Manual                     |
| **CLI Toolchain Integration** | Complete (`eza`, `fzf`, `zoxide`, `delta`, `fd`) | Focused (`zoxide`, `fzf`)         | None (Prompt only)         | Varies                     |
| **Version & Diagnostics**     | Built-in (`nirmana version` & `doctor`)          | Basic Script Checks               | `oh-my-posh version`       | None                       |

### Key Distinctions

- **Versus Chris Titus Tech (`win-dotfiles`):** While `win-dotfiles` offers a proven system-wide setup tailored to general Windows utilities with a single static Starship theme, Nirmana-Shell focuses exclusively on the terminal developer experience: providing an interactive 27-theme TUI switcher, right-aligned `$fill` layouts, automated visual galleries, and full Delta git pager integration.
- **Versus Oh My Posh:** Oh My Posh is an outstanding prompt engine with a vast collection of community themes. However, Oh My Posh is solely a prompt engine. Nirmana-Shell integrates Starship into a cohesive terminal ecosystem that configures PSReadLine, predictive completions, syntax-highlighted git diffs, directory jumping, and automatic Windows Terminal color scheme synchronization.
- **Versus Standalone Dotfiles / Community Presets:** Standalone dotfiles require manual package installations, manual font configuration, and editing TOML files by hand. Nirmana-Shell packages everything into an automated, idempotent setup with self-healing profile reloaders and versioned health checks.

---

## Repository Layout

```text
nirmana-shell/
├── LICENSE                 # MIT license and acknowledgements
├── README.md               # Documentation
├── VERSION                 # Single source of truth for version number
├── CHANGELOG.md            # Standard Keep a Changelog documentation
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

- Starship (ISC License): https://starship.rs
- Zoxide (MIT License): https://github.com/ajeetdsouza/zoxide
- Eza (EUPL-1.2 License): https://github.com/eza-community/eza
- FZF (MIT License): https://github.com/junegunn/fzf
- Delta (MIT License): https://github.com/dandavison/delta
- FD (MIT/Apache-2.0 License): https://github.com/sharkdp/fd
- PSReadLine (MIT License): https://github.com/PowerShell/PSReadLine
