# Tridatu-Shell

Automated modern terminal setup untuk Windows berbasis **PowerShell 7**, **Starship**, **PSReadLine**, **Zoxide**, **Eza**, **FZF**, **Delta**, dan **FD**.

---

## Quick Start (Instalasi 1 Perintah)

Buka PowerShell (*Run as Administrator* disarankan), lalu jalankan:

### Opsi A: Instalasi Online (via GitHub)
```powershell
irm https://raw.githubusercontent.com/Andndre/tridatu-shell/main/setup.ps1 | iex
```

### Opsi B: Instalasi Lokal
Jika menyalin folder proyek ini secara langsung:
```powershell
cd tridatu-shell
.\setup.ps1
```

Script akan otomatis:
1. Memasang seluruh tools via WinGet (`pwsh`, `starship`, `zoxide`, `eza`, `fzf`, `delta`, `fd`).
2. Mengonfigurasi Git Pager ke `delta` untuk syntax-highlighted diffs.
3. Memasang profil PowerShell 7 dan konfigurasi Starship.
4. Mematikan suara alert bell saat backspace di baris kosong.
5. Menyetel PowerShell 7 sebagai default profile di Windows Terminal.

---

## Prasyarat: Nerd Font

Semua ikon Starship dan Eza membutuhkan Nerd Font.

1. Pasang font via WinGet:
   ```cmd
   winget install Microsoft.CascadiaCodeNF
   ```
2. Di **Windows Terminal**: Buka **Settings (Ctrl + ,)** -> **Defaults** -> **Appearance** -> **Font face** -> Pilih **`CaskaydiaCove NF`**.

---

## Fitur & Pintasan Keyboard

| Fitur | Pintasan / Perintah | Keterangan |
| :--- | :--- | :--- |
| **Inline Autocomplete** | Teks abu-abu otomatis | Saran riwayat perintah ala Fish-shell |
| **Terima Seluruh Saran** | `→` (Panah Kanan) / `End` | Menerima seluruh teks prediksi |
| **Terima Per Kata** | `Ctrl + F` | Menerima prediksi kata demi kata |
| **Toggle Tampilan Saran**| `F2` | Beralih antara *InlineView* (1 baris) dan *ListView* (dropdown) |
| **Interactive History** | `Ctrl + R` | Fullscreen fuzzy search riwayat perintah via `fzf` |
| **Menu Completion** | `Tab` | Grid menu interaktif untuk file/parameter |
| **Smart Directory Jump** | `z <nama_folder>` | Lompat ke folder mana pun lintas drive |
| **Interactive Jump** | `zi` | Menu seleksi direktori interaktif via `fzf` |
| **Modern File Listing** | `ls`, `ll`, `la`, `lt` | Pengganti `ls` via `eza` (ikon + warna) |
| **Enhanced Git Diff** | `git diff`, `git show` | Visual diff dua sisi dengan nomor baris via `delta` |
| **Fast File Search** | `fd <nama_file>` | Pencarian file cepat (otomatis abaikan `.git` & `node_modules`) |
| **Silent Backspace** | `Backspace` | Hening tanpa suara beep alert Windows |

---

## Perintah CLI `tridatu-shell`

Setelah terpasang, perintah `tridatu-shell` (atau alias `tridatu`) dapat diakses langsung dari mana saja di terminal:

| Perintah | Deskripsi |
| :--- | :--- |
| `tridatu-shell theme` | Buka menu interaktif `fzf` untuk memilih dan mengganti tema Starship |
| `tridatu-shell theme <nama>` | Ganti ke tema tertentu secara instan (mendukung Tab autocomplete) |
| `tridatu-shell doctor` | Periksa kesehatan seluruh utilitas CLI (`pwsh`, `starship`, `zoxide`, `eza`, `fzf`, `delta`, `fd`, `rg`) |
| `tridatu-shell update` | Perbarui konfigurasi dan tema Tridatu-Shell ke versi terbaru dari GitHub |
| `tridatu-shell reload` | Muat ulang `$PROFILE` PowerShell pada tab aktif |

### Pilihan Tema Bawaan:
* **`tridatu`** (Default)
* **`tokyo-night`**
* **`catppuccin-mocha`**
* **`minimal-emerald`**

Contoh pemakaian:
```powershell
tridatu-shell theme tokyo-night
```
*(Tip: Anda juga bisa mengetik `tridatu theme` atau menekan `Tab` setelah kata `theme` untuk autocomplete nama tema).*

---

## Struktur Folder

```text
tridatu-shell/
├── README.md               # Dokumentasi instalasi dan penggunaan
├── setup.ps1               # Script instalasi otomatis (One-liner)
├── switch-theme.ps1        # Script ganti tema Starship
├── configs/
│   └── Microsoft.PowerShell_profile.ps1 # File profil PowerShell 7
└── themes/
    ├── tridatu.toml
    ├── tokyo-night.toml
    ├── catppuccin-mocha.toml
    └── minimal-emerald.toml
```

---

## Cara Share ke GitHub

1. Buat repository baru di GitHub bernama `tridatu-shell`.
2. Push folder ini:
   ```bash
   cd D:\tridatu-shell
   git init
   git add .
   git commit -m "feat: initial commit tridatu-shell"
   git remote add origin https://github.com/Andndre/tridatu-shell.git
   git branch -M main
   git push -u origin main
   ```
3. Ganti `Andndre` pada URL one-liner di file README ini dengan username GitHub Anda.
