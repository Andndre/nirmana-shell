#!/usr/bin/env python3
"""
Generate PNG preview cards for Nirmana-Shell themes from .previews/*.txt
Uses Rich and resvg-py to rasterize ANSI prompts into pixel-perfect PNGs.
"""

import glob
import io
import os
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.text import Text
    import resvg_py
except ImportError:
    print("Dependencies missing. Run with:")
    print("uv run --with rich --with resvg-py python scripts/generate-previews.py")
    sys.exit(1)


def find_nerd_fonts() -> list[str]:
    """Discover installed Nerd Fonts on Windows."""
    search_dirs = [
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts"),
        os.path.expandvars(r"%WINDIR%\Fonts"),
    ]
    fonts = []
    for d in search_dirs:
        if os.path.isdir(d):
            # Prefer CaskaydiaCove NF or any Nerd Font
            for pattern in ("*Caskaydia*Nerd*.ttf", "*Nerd*.ttf", "*NF*.ttf"):
                found = glob.glob(os.path.join(d, pattern))
                fonts.extend(found)
    # Deduplicate while preserving order
    seen = set()
    unique_fonts = []
    for f in fonts:
        if f.lower() not in seen:
            seen.add(f.lower())
            unique_fonts.append(f)
    return unique_fonts


def extract_prompt_lines(raw_text: str) -> str:
    """Extract rendered prompt lines from .previews text file."""
    lines = raw_text.splitlines()
    capturing = False
    prompt_lines = []

    for line in lines:
        if "Rendered Prompt:" in line:
            capturing = True
            continue
        if capturing:
            # Stop when hitting the bottom separator
            if "───" in line:
                break
            prompt_lines.append(line)

    content = "\n".join(prompt_lines).strip("\r\n")
    return content if content else raw_text


def generate_preview_png(txt_path: Path, output_dir: Path, font_files: list[str]) -> Path:
    """Render a single theme preview text to PNG."""
    theme_name = txt_path.stem
    raw_text = txt_path.read_text(encoding="utf-8")
    prompt_text = extract_prompt_lines(raw_text)

    # Render via Rich Console to SVG with sufficient width to prevent
    # artificial wrapping of wide 1-line ribbon presets (e.g. catppuccin-powerline)
    stream = io.StringIO()
    console = Console(record=True, file=stream, width=96)
    console.print(Text.from_ansi(prompt_text))
    svg_data = console.export_svg(title=theme_name)

    # CRITICAL: Rich hardcodes 'font-family: Fira Code, monospace' in its SVG CSS.
    # resvg-py respects the CSS font-family over the parameter. If Fira Code isn't replaced,
    # resvg falls back to Windows system monospace (MS Gothic / Consolas), which maps
    # Nerd Font PUA code points to Chinese kanji (e.g. ㊝) and corrupts powerline chevrons.
    font_family_name = "CaskaydiaCove NF"
    svg_data = svg_data.replace("Fira Code", font_family_name)

    # Rasterize SVG to PNG using resvg-py
    png_bytes = resvg_py.svg_to_bytes(
        svg_string=svg_data,
        font_files=font_files if font_files else None,
        font_family=font_family_name,
    )

    out_file = output_dir / f"{theme_name}.png"
    out_file.write_bytes(png_bytes)
    return out_file


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate PNG preview cards for Nirmana-Shell themes.")
    parser.add_argument("-t", "--theme", help="Specific theme name to generate preview for (stem of .txt)")
    parser.add_argument("--force", action="store_true", help="Regenerate even if PNG exists and is newer than .txt")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    preview_dir = repo_root / ".previews"
    output_dir = repo_root / "assets" / "previews"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not preview_dir.exists():
        print(f"Error: Preview directory not found: {preview_dir}")
        sys.exit(1)

    if args.theme:
        target_txt = preview_dir / f"{args.theme}.txt"
        if not target_txt.exists():
            print(f"Error: Preview file not found: {target_txt}")
            sys.exit(1)
        txt_files = [target_txt]
    else:
        txt_files = sorted(preview_dir.glob("*.txt"))
        if not args.force:
            pending = []
            for t in txt_files:
                png_path = output_dir / f"{t.stem}.png"
                if not png_path.exists() or png_path.stat().st_mtime < t.stat().st_mtime:
                    pending.append(t)
            txt_files = pending

    if not txt_files:
        print("All preview PNGs are already up to date.")
        return

    nerd_fonts = find_nerd_fonts()
    if nerd_fonts:
        print(f"Using font: {nerd_fonts[0]}")
    else:
        print("Warning: No local Nerd Font found, falling back to system fonts.")

    print(f"Generating {len(txt_files)} preview PNGs in {output_dir}...")
    for idx, txt_path in enumerate(txt_files, 1):
        out = generate_preview_png(txt_path, output_dir, nerd_fonts)
        size_kb = out.stat().st_size / 1024
        print(f"[{idx:02d}/{len(txt_files):02d}] {txt_path.stem:<28} -> {out.name} ({size_kb:.1f} KB)")

    print(f"\nCompleted successfully! Generated {len(txt_files)} images.")


if __name__ == "__main__":
    main()
