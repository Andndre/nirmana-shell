#!/usr/bin/env python3
"""
Nirmana-Shell - Oh My Posh to Starship Theme Transpiler (Version 3.1)
Converts Oh My Posh theme JSON configurations (*.omp.json) into clean,
high-performance Starship themes (*.toml) with zero-seam powerline ribbons,
resilient dual-capsule left prompts, multi-line block fidelity, and full
support for modern Starship features (such as prev_bg from PR #6017).
"""

import argparse
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

GO_DATE_TO_STRFTIME = [
    ("Monday", "%A"),
    ("Mon", "%a"),
    ("January", "%B"),
    ("Jan", "%b"),
    ("2006", "%Y"),
    ("06", "%y"),
    ("01", "%m"),
    ("1", "%m"),
    ("02", "%d"),
    ("2", "%d"),
    ("15", "%H"),
    ("03", "%I"),
    ("3", "%I"),
    ("04", "%M"),
    ("4", "%M"),
    ("05", "%S"),
    ("5", "%S"),
    ("PM", "%p"),
    ("pm", "%p"),
    ("MST", "%Z"),
]

OMP_COLOR_MAP = {
    "lightyellow": "#FFF59D",
    "lightblue": "#80D8FF",
    "lightgreen": "#A5D6A7",
    "lightcyan": "#80DEEA",
    "lightmagenta": "#F48FB1",
    "lightred": "#FF8A80",
    "lightwhite": "#FFFFFF",
    "lightblack": "#757575",
    "darkgray": "#616161",
    "darkgrey": "#616161",
    "gray": "#9E9E9E",
    "grey": "#9E9E9E",
    "darkred": "#C62828",
    "darkgreen": "#2E7D32",
    "darkblue": "#1565C0",
    "darkcyan": "#00838F",
    "darkmagenta": "#6A1B9A",
    "darkyellow": "#F9A825",
    "white": "#FFFFFF",
    "black": "#000000",
    "red": "#FF5252",
    "green": "#69F0AE",
    "blue": "#448AFF",
    "yellow": "#FFD740",
    "magenta": "#FF4081",
    "cyan": "#18FFFF",
}

RUNTIME_MAPPINGS = {
    "node": ("nodejs", "$nodejs", "󰎙 ", "#80D166"),
    "nodejs": ("nodejs", "$nodejs", "󰎙 ", "#80D166"),
    "go": ("golang", "$golang", " ", "#06AAD5"),
    "golang": ("golang", "$golang", " ", "#06AAD5"),
    "python": ("python", "$python", "󰌠 ", "#FFE873"),
    "rust": ("rust", "$rust", " ", "#F78C6C"),
    "ruby": ("ruby", "$ruby", " ", "#FF5874"),
    "java": ("java", "$java", " ", "#EC2729"),
    "dotnet": ("dotnet", "$dotnet", "󰪮 ", "#0D6DA8"),
    "php": ("php", "$php", " ", "#787CB5"),
    "bun": ("bun", "$bun", "󰎙 ", "#FF9F43"),
    "deno": ("deno", "$deno", " ", "#7FD5EA"),
    "dart": ("dart", "$dart", " ", "#7FD5EA"),
    "julia": ("julia", "$julia", " ", "#945BB3"),
    "package": ("package", "$package", "󰏗 ", "#AEA4BF"),
    "c": ("c", "$c", " ", "#00599C"),
    "cpp": ("cpp", "$cpp", " ", "#00599C"),
    "kotlin": ("kotlin", "$kotlin", " ", "#F18E33"),
    "scala": ("scala", "$scala", " ", "#DC322F"),
    "haskell": ("haskell", "$haskell", " ", "#5E5086"),
    "elixir": ("elixir", "$elixir", " ", "#4E2A8E"),
    "elm": ("elm", "$elm", " ", "#60B5CC"),
    "erlang": ("erlang", "$erlang", " ", "#A90533"),
    "lua": ("lua", "$lua", " ", "#000080"),
    "zig": ("zig", "$zig", " ", "#F7A41D"),
    "nim": ("nim", "$nim", "󰆥 ", "#FFE953"),
    "crystal": ("crystal", "$crystal", " ", "#000000"),
    "docker": ("docker_context", "$docker_context", " ", "#2496ED"),
    "docker_context": ("docker_context", "$docker_context", " ", "#2496ED"),
    "kubernetes": ("kubernetes", "$kubernetes", "󱃾 ", "#326CE5"),
    "terraform": ("terraform", "$terraform", "󱁢 ", "#844FBA"),
    "aws": ("aws", "$aws", " ", "#FF9900"),
    "az": ("azure", "$azure", " ", "#008AD7"),
    "azure": ("azure", "$azure", " ", "#008AD7"),
    "gcloud": ("gcloud", "$gcloud", "󱇶 ", "#4285F4"),
    "conda": ("conda", "$conda", " ", "#44A833"),
}

STANDARD_DEVELOPER_RUNTIMES = [
    ("nodejs", "$nodejs", "󰎙 ", "#80D166"),
    ("python", "$python", "󰌠 ", "#FFE873"),
    ("golang", "$golang", " ", "#06AAD5"),
    ("rust", "$rust", " ", "#F78C6C"),
    ("php", "$php", " ", "#787CB5"),
    ("package", "$package", "󰏗 ", "#AEA4BF"),
]


def convert_go_date_format(go_fmt: str) -> str:
    """Convert Go time reference format to strftime format."""
    res = re.sub(r"<[^>]+>", "", go_fmt)
    for go_pat, strftime_pat in GO_DATE_TO_STRFTIME:
        res = re.sub(r"\b" + re.escape(go_pat) + r"\b", strftime_pat, res)
    return res


def parse_omp_markup(text: Optional[str], default_fg: Optional[str] = None) -> str:
    """Convert Oh My Posh diamond/template markup (<#hex>text</>) to Starship styled spans."""
    if not text:
        return ""
    cleaned = re.sub(r"\{\{.*?\}\}", "", text)
    if not cleaned.strip():
        return ""

    spans = []
    pos = 0
    pattern = re.compile(r"<([#a-zA-Z0-9_\-]+)>(.*?)</>")
    for m in pattern.finditer(cleaned):
        if m.start() > pos:
            plain = cleaned[pos:m.start()]
            if plain:
                fg_spec = f"bold {default_fg}" if default_fg else "bold"
                spans.append(f"[{plain}]({fg_spec})")
        col = m.group(1)
        content = m.group(2)
        if content:
            spans.append(f"[{content}](bold {col})")
        pos = m.end()
    if pos < len(cleaned):
        plain = cleaned[pos:]
        if plain:
            fg_spec = f"bold {default_fg}" if default_fg else "bold"
            spans.append(f"[{plain}]({fg_spec})")
    return "".join(spans)


def parse_omp_json(source: str) -> Tuple[Dict[str, Any], str]:
    """Load JSON from local file, remote URL, or Oh My Posh official theme name."""
    theme_name = ""
    url = source
    if not source.startswith("http://") and not source.startswith("https://"):
        path = Path(source)
        if not path.exists():
            candidate_name = source.replace(".omp.json", "").replace(".json", "")
            url = f"https://raw.githubusercontent.com/JanDeDobbeleer/oh-my-posh/main/themes/{candidate_name}.omp.json"
            theme_name = candidate_name
        else:
            data = path.read_text(encoding="utf-8")
            theme_name = path.stem.replace(".omp", "")
            return json.loads(data), theme_name

    if url.startswith("http://") or url.startswith("https://"):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Nirmana-Shell-Transpiler/3.1"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read().decode("utf-8")
                if not theme_name:
                    theme_name = Path(url.split("?")[0]).stem.replace(".omp", "")
                return json.loads(data), theme_name
        except Exception as e:
            print(f"Error fetching Oh My Posh theme '{source}': {e}", file=sys.stderr)
            sys.exit(1)


class OmpTranspiler:
    def __init__(
        self,
        data: Dict[str, Any],
        theme_name: str,
        use_fill: bool = True,
        left_style_override: Optional[str] = None,
        use_pills: bool = False,
        ribbon_bg_override: Optional[str] = None,
        add_runtimes: bool = True,
        force_runtimes: bool = False,
    ):
        self.data = data
        self.theme_name = theme_name
        self.use_fill = use_fill
        self.left_style_override = left_style_override
        self.use_pills = use_pills
        self.ribbon_bg_override = ribbon_bg_override
        self.add_runtimes = add_runtimes
        self.force_runtimes = force_runtimes
        self.palette = data.get("palette", {})
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.has_top_connector = False
        self.char_is_plain = False

    def resolve_color(self, col: Optional[str]) -> Optional[str]:
        """Resolve hex, named, or palette-referenced colors to clean hex strings."""
        if not col:
            return None
        col = str(col).strip()
        if col.lower() == "transparent":
            return None
        if col.startswith("p:"):
            key = col[2:]
            col = self.palette.get(key, key)
        elif col in self.palette:
            col = self.palette[col]

        if not col or str(col).strip().lower() == "transparent":
            return None

        c_lower = str(col).strip().lower()
        if c_lower in OMP_COLOR_MAP:
            return OMP_COLOR_MAP[c_lower]

        h = col[1:] if col.startswith("#") else col
        if len(h) == 3 and all(c in "0123456789abcdefABCDEF" for c in h):
            return f"#{h[0]*2}{h[1]*2}{h[2]*2}"
        elif len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h):
            return f"#{h}"
        elif len(h) == 8 and all(c in "0123456789abcdefABCDEF" for c in h):
            return f"#{h[:6]}"
        return col

    def get_seg_colors(self, seg: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Extract foreground and background colors with template fallback support."""
        fg = self.resolve_color(seg.get("foreground"))
        bg = self.resolve_color(seg.get("background"))

        if not bg and "background_templates" in seg:
            for bt in seg["background_templates"]:
                m = re.search(r"(?:#([0-9a-fA-F]{3,6})|p:([a-zA-Z0-9_\-]+))", bt)
                if m:
                    bg = self.resolve_color(f"#{m.group(1)}" if m.group(1) else f"p:{m.group(2)}")
                    if bg:
                        break

        if not fg and "foreground_templates" in seg:
            for ft in seg["foreground_templates"]:
                m = re.search(r"(?:#([0-9a-fA-F]{3,6})|p:([a-zA-Z0-9_\-]+))", ft)
                if m:
                    fg = self.resolve_color(f"#{m.group(1)}" if m.group(1) else f"p:{m.group(2)}")
                    if fg:
                        break

        return fg, bg

    def transpile(self) -> str:
        blocks = self.data.get("blocks", [])
        if not blocks:
            return ""

        all_segs = [s for b in blocks for s in b.get("segments", [])]

        # Step 1: Detect Overall Theme Visual Style
        has_any_bg = any(self.get_seg_colors(s)[1] is not None for s in all_segs)

        has_bracket_frame = any(
            any(c in s.get("template", "") for c in ("\u250f", "┏", "\u2514", "┗", "\u2516", "┖"))
            for s in all_segs
        )

        has_rounded_powerline = any(s.get("powerline_symbol") == "\ue0b4" for s in all_segs)
        pixel_powerline_count = sum(
            1 for s in all_segs
            if s.get("powerline_symbol") in ("\ue0c4", "\ue0c5") or
            any(g in (s.get("leading_diamond", "") + s.get("trailing_diamond", "")) for g in ("\ue0c6", "\ue0c7"))
        )
        rounded_powerline_count = sum(1 for s in all_segs if s.get("powerline_symbol") == "\ue0b4")
        has_pixel_powerline = pixel_powerline_count > 0 and pixel_powerline_count >= rounded_powerline_count

        is_flat_ribbon = False
        if len(all_segs) >= 3 and not has_rounded_powerline and not has_pixel_powerline:
            b0_segs = blocks[0].get("segments", []) if blocks else []
            if b0_segs and b0_segs[0].get("leading_diamond") == "\ue0b6":
                plain_bg_count = sum(1 for s in b0_segs[1:] if s.get("style") == "plain" and self.get_seg_colors(s)[1])
                if plain_bg_count >= 2:
                    is_flat_ribbon = True

        powerline_count = sum(
            1 for s in all_segs
            if any(g in (s.get("leading_diamond", "") + s.get("trailing_diamond", "") + s.get("powerline_symbol", "") + s.get("template", "")) for g in ("\ue0b0", "\ue0b2", "\ue0b1", "\ue0b3", "\ue0c4", "\ue0c5", "\ue0c0", "\ue0c2"))
        )
        capsule_count = sum(
            1 for s in all_segs
            if any(g in (s.get("leading_diamond", "") + s.get("trailing_diamond", "")) for g in ("\ue0b6", "\ue0b4"))
        )
        has_pill_diamonds = sum(
            1 for s in all_segs
            if "\ue0b6" in s.get("leading_diamond", "") and "\ue0b4" in s.get("trailing_diamond", "")
        ) >= 2

        self.has_top_connector = any(
            any(c in (s.get("leading_diamond", "") + s.get("template", "")) for c in ("\u256d", "╭"))
            for s in all_segs
        )

        self.powerline_symbol = "\ue0b0"
        self.has_bracket_frame = has_bracket_frame
        self.bracket_fg = "#CB4B16"
        if has_bracket_frame:
            for s in all_segs:
                m_b = re.search(r"<([#a-zA-Z0-9_\-]+)>[┏┖┗\u250f\u2514\u2516\[]", s.get("template", ""))
                if m_b:
                    self.bracket_fg = self.resolve_color(m_b.group(1)) or self.bracket_fg
                    break
            theme_style = "bracket_frame"
            self.use_fill = False
        elif has_pixel_powerline:
            theme_style = "powerline"
            self.powerline_symbol = "\ue0c4"
        elif has_rounded_powerline:
            theme_style = "powerline"
            self.powerline_symbol = "\ue0b4"
        elif is_flat_ribbon:
            theme_style = "powerline"
            self.powerline_symbol = ""
        elif not has_any_bg:
            theme_style = "flat"
        elif has_pill_diamonds:
            theme_style = "capsule"
        elif powerline_count >= capsule_count and powerline_count > 0:
            theme_style = "powerline"
            self.powerline_symbol = "\ue0b0"
        elif capsule_count > 0:
            theme_style = "capsule"
        else:
            theme_style = "capsule" if has_any_bg else "flat"

        if self.left_style_override:
            theme_style = self.left_style_override

        # Step 2: Group blocks into physical lines
        has_block_diamonds = any(b.get("leading_diamond") for b in blocks)
        if has_block_diamonds:
            self.use_fill = False

        prompt_lines: List[Dict[str, List[Dict[str, Any]]]] = []

        if has_block_diamonds:
            # Group framed blocks by level:
            # Level 0 (Header): blocks with ┏ or ╭
            # Level 1 (Body): all intermediate blocks (sharing ┣ or │), combining path, git, cloud, runtimes
            # Level 2 (Footer): block with └ or ╰ (character line)
            header_segs = []
            body_segs = []
            footer_segs = []
            header_lead = ""
            body_lead = ""
            footer_lead = ""

            for b in blocks:
                lead_dia = b.get("leading_diamond", "")
                lead_markup = parse_omp_markup(lead_dia) if lead_dia else ""
                segs = list(b.get("segments", []))
                if any(c in lead_dia for c in ("\u250f", "┏", "\u256d", "╭")):
                    if not header_lead:
                        header_lead = lead_markup
                    header_segs.extend(segs)
                elif any(c in lead_dia for c in ("\u2514", "└", "\u2570", "╰")):
                    if not footer_lead:
                        footer_lead = lead_markup
                    footer_segs.extend(segs)
                else:
                    if not body_lead and lead_markup:
                        body_lead = lead_markup
                    body_segs.extend(segs)

            # Insert connectors at the start of each line
            if header_lead:
                header_segs.insert(0, {"type": "block_connector", "markup": header_lead})
            if body_lead:
                body_segs.insert(0, {"type": "block_connector", "markup": body_lead})
            if footer_lead:
                footer_segs.insert(0, {"type": "block_connector", "markup": footer_lead})

            # Ensure navigation (path/git) comes before cloud/tool segments on body line if present
            nav_segs = [s for s in body_segs if s.get("type") in ("path", "git")]
            other_segs = [s for s in body_segs if s.get("type") not in ("path", "git", "block_connector")]
            conn_seg = [s for s in body_segs if s.get("type") == "block_connector"]
            body_segs = conn_seg + nav_segs + other_segs

            prompt_lines.append({"left": header_segs, "right": []})
            if body_segs:
                prompt_lines.append({"left": body_segs, "right": []})
            if footer_segs:
                prompt_lines.append({"left": footer_segs, "right": []})
        else:
            curr_line: Dict[str, List[Dict[str, Any]]] = {"left": [], "right": []}
            for idx, b in enumerate(blocks):
                lead_dia = b.get("leading_diamond")
                lead_markup = parse_omp_markup(lead_dia) if lead_dia else ""

                if idx > 0 and b.get("newline"):
                    prompt_lines.append(curr_line)
                    curr_line = {"left": [], "right": []}

                align = b.get("alignment", "left")
                if b.get("type") == "rprompt":
                    align = "right"

                segs = list(b.get("segments", []))
                if lead_markup and align == "left":
                    segs.insert(0, {"type": "block_connector", "markup": lead_markup})

                curr_line[align].extend(segs)

            prompt_lines.append(curr_line)

        # OMP Rule: If a line has NO left-aligned segments, right-aligned blocks render as left-aligned!
        for pl in prompt_lines:
            if not pl["left"] and pl["right"]:
                pl["left"] = pl["right"]
                pl["right"] = []

        # Guard: If line 1 left is empty but line 1 right contains navigation/identity modules, relocate to left
        nav_types = ("path", "git", "os", "root")
        if not prompt_lines[0]["left"]:
            nav_segs = [s for s in prompt_lines[0]["right"] if s.get("type") in nav_types]
            if nav_segs:
                prompt_lines[0]["left"].extend(nav_segs)
                prompt_lines[0]["right"] = [s for s in prompt_lines[0]["right"] if s.get("type") not in nav_types]

        is_single_line = len(prompt_lines) <= 1

        # Dedup modules between lines in multi-line prompts (e.g. cloud-context)
        if len(prompt_lines) > 1:
            later_types = set()
            for pl in prompt_lines[1:]:
                for s in pl["left"]:
                    st = s.get("type")
                    if st in ("git", "time", "path"):
                        later_types.add(st)
            prompt_lines[0]["left"] = [s for s in prompt_lines[0]["left"] if s.get("type") not in later_types]

        if len(prompt_lines) >= 3 and any(s.get("type") == "path" for s in prompt_lines[1]["left"]):
            prompt_lines[1]["left"] = [s for s in prompt_lines[1]["left"] if s.get("type") != "time"]

        # Step 3: Extract prompt character from the last line (status or text segment)
        line_character = None
        has_pill_prompt_user = False
        last_left = prompt_lines[-1]["left"] if prompt_lines else []
        connector_span = ""
        for s in list(last_left):
            stype = s.get("type")
            tmpl = s.get("template", "")
            fg, bg = self.get_seg_colors(s)
            if stype == "block_connector":
                connector_span = s.get("markup", "")
                last_left.remove(s)
                break
            elif stype in ("text", "status") and any(c in tmpl for c in ("\u2570", "╰")):
                col = fg or bg or "#FEF5ED"
                connector_span = f"[{tmpl.strip()}](fg:{col})"
                last_left.remove(s)
                break

        # Check for pixelated badge cap + prompt character in last_left (e.g. cloud-context)
        for i, s in enumerate(list(last_left)):
            if s.get("type") == "root" and s.get("leading_diamond") in ("\ue0c7", "") and s.get("trailing_diamond") in ("\ue0c6", ""):
                next_s = last_left[i + 1] if i + 1 < len(last_left) else None
                if next_s and any(c in next_s.get("template", "") for c in (">", "❯", "➜", "\u276f")):
                    fg_badge, bg_badge = self.get_seg_colors(s)
                    b_col = bg_badge or "#dd0033"
                    t_col = fg_badge or "#151515"
                    char_fg = self.get_seg_colors(next_s)[0] or "#ffffff"
                    line_character = {
                        "format": "$symbol",
                        "success_symbol": f"[](fg:{b_col})[ ⚡ ](fg:{t_col} bg:{b_col})[](fg:{b_col})[ > ](bold {char_fg})",
                        "error_symbol": f"[](fg:{b_col})[ ⚡ ](fg:{t_col} bg:{b_col})[](fg:{b_col})[ > ](bold #ef5350)",
                    }
                    last_left.remove(s)
                    last_left.remove(next_s)
                    break

        if has_bracket_frame and not line_character:
            bracket_fg = getattr(self, "bracket_fg", "#CB4B16")
            line_character = {
                "format": "$symbol",
                "success_symbol": f"[> ](fg:{bracket_fg})",
                "error_symbol": f"[> ](fg:{bracket_fg})",
            }

        for s in reversed(last_left):
            stype = s.get("type")
            tmpl = s.get("template", "")
            fg, bg = self.get_seg_colors(s)
            lead = s.get("leading_diamond", "")
            trail = s.get("trailing_diamond", "")
            has_prompt_char = any(c in tmpl for c in ("\u276f", "\u276e", "❯", "❮", ">", "$", "#", "➜", "➔", "\u279c", "λ", "", "", "▶", "»", "\u2b9e", "⮞"))
            is_ribbon_status = (stype == "status" and (bg or s.get("trailing_diamond") or s.get("powerline_symbol")) and not has_prompt_char)
            if (stype == "text" or (stype == "status" and not is_ribbon_status)) or (stype == "session" and has_prompt_char):
                clean_sym = re.sub(r"\{\{.*?\}\}", "", tmpl)
                clean_sym = re.sub(r"<[^>]+>", "", clean_sym).strip()
                if clean_sym == "\u279c":
                    clean_sym = "➔ " 
                if len(clean_sym) > 4 and not any(k in tmpl for k in ("{{ .UserName }}", ".UserName")):
                    continue
                clean_sym = clean_sym.replace("\\", "").replace("$", "\\$")
                clean_sym = clean_sym.replace("[", "\\[").replace("]", "\\]")
                clean_sym = clean_sym.replace("(", "\\(").replace(")", "\\)")
                sym = f"{clean_sym} " if clean_sym else "❯ "

                col = fg or bg or "#22da6e"
                err_col = "#ef5350"
                for t in s.get("foreground_templates", []):
                    m = re.search(r"#([0-9a-fA-F]{3,6})", t)
                    if m:
                        err_col = f"#{m.group(1)}"
                        break

                has_user = any(k in tmpl for k in ("{{ .UserName }}", ".UserName", "{{.UserName}}"))
                is_pill_prompt = bg and ("\ue0b6" in lead or "\ue0b4" in trail or has_pill_diamonds)

                if is_pill_prompt and has_user:
                    has_pill_prompt_user = True
                    self.modules["username"] = {
                        "style_user": f"fg:{fg or '#ffffff'} bg:{bg}",
                        "style_root": f"fg:#FFEB3B bg:{bg}",
                        "format": f"[](fg:{bg})[ $user ]($style)",
                        "show_always": True,
                    }
                    line_character = {
                        "format": "$symbol",
                        "success_symbol": f"[{sym}](bold {col} bg:{bg})[](fg:{bg}) ",
                        "error_symbol": f"[{sym}](bold {err_col} bg:{bg})[](fg:{bg}) ",
                    }
                elif is_pill_prompt:
                    line_character = {
                        "format": "$symbol",
                        "success_symbol": f"[](fg:{bg})[ {sym}](bold {col} bg:{bg})[](fg:{bg}) ",
                        "error_symbol": f"[](fg:{bg})[ {sym}](bold {err_col} bg:{bg})[](fg:{bg}) ",
                    }
                else:
                    self.char_is_plain = (s.get("style") == "plain")
                    line_character = {
                        "success_symbol": f"[{sym}](bold {col}) ",
                        "error_symbol": f"[{sym}](bold {err_col}) ",
                    }
                    if connector_span:
                        line_character["format"] = f"{connector_span}$symbol"

                last_left.remove(s)
                break

        if not line_character:
            if connector_span:
                line_character = {
                    "format": f"{connector_span} $symbol",
                    "success_symbol": "",
                    "error_symbol": "[x ](bold #ef5350)",
                }
            else:
                line_character = {
                    "success_symbol": "[❯ ](bold #22da6e) ",
                    "error_symbol": "[❯ ](bold #ef5350) ",
                }
        self.modules["character"] = line_character

        # Step 4: Process Line 1
        line1_left = prompt_lines[0]["left"]
        line1_right = prompt_lines[0]["right"]

        # Relocate metrics and runtimes from left to right on Line 1 ONLY if Line 1 has project identity and right side is initially empty
        has_project_identity = any(s.get("type") in ("path", "git") for s in line1_left)
        is_continuous_ribbon = (
            has_rounded_powerline or is_flat_ribbon or has_pixel_powerline or
            (theme_style == "powerline" and powerline_count > 0 and not has_pill_diamonds)
        )
        is_multiline_prompt = len(prompt_lines) > 1 and any(pl["left"] for pl in prompt_lines[1:])

        has_dir_l1 = any(s.get("type") == "path" for s in line1_left)
        if theme_style == "powerline" and has_dir_l1:
            line1_left = [s for s in line1_left if s.get("type") != "time"]
            prompt_lines[0]["left"] = [s for s in prompt_lines[0]["left"] if s.get("type") != "time"]

        if (has_project_identity and has_dir_l1 and not has_block_diamonds and not line1_right and
            not is_continuous_ribbon and
            not has_bracket_frame and
            not (is_multiline_prompt and len(prompt_lines) >= 3)):
            relocated = []
            remaining_l1 = []
            for s in line1_left:
                stype = s.get("type", "")
                if stype in ("executiontime", "sysinfo", "memory", "battery", "time") or stype in ("nodejs", "python", "golang", "rust", "php", "ruby", "java", "dotnet", "package"):
                    relocated.append(s)
                    continue
                remaining_l1.append(s)
            prompt_lines[0]["left"] = remaining_l1
            if relocated:
                line1_right[:0] = relocated

        # Check if runtimes should be injected
        has_orig_runtimes = any(s.get("type") in RUNTIME_MAPPINGS for s in all_segs)
        should_inject_runtimes = not has_block_diamonds and (
            self.force_runtimes or (self.add_runtimes and has_orig_runtimes)
        )
        if (not line1_right and not self.force_runtimes) and (
            is_continuous_ribbon or has_bracket_frame or not has_dir_l1 or not has_project_identity
        ):
            should_inject_runtimes = False

        # Parse Line 1 Left segments
        parsed_l1_left = []
        for s in prompt_lines[0]["left"]:
            mod = self.parse_segment(s)
            if mod:
                if parsed_l1_left and parsed_l1_left[-1]["mod_name"] == mod["mod_name"]:
                    if parsed_l1_left[-1].get("leading") and not mod.get("leading"):
                        mod["leading"] = parsed_l1_left[-1]["leading"]
                    parsed_l1_left[-1] = mod
                else:
                    parsed_l1_left.append(mod)

        # Check if directory or git are missing completely across all lines
        all_parsed_segs = [self.parse_segment(s) for pl in prompt_lines for s in pl["left"] + pl["right"]]
        all_parsed_names = {p["mod_name"] for p in all_parsed_segs if p}

        if "directory" not in all_parsed_names and not has_block_diamonds:
            parsed_l1_left.insert(0, {
                "mod_name": "directory", "var_name": "$directory",
                "fg": "#82AAFF" if theme_style == "flat" else "#011627",
                "bg": None if theme_style == "flat" else "#82AAFF",
                "leading": "" if theme_style == "flat" else "╭─",
                "trailing": "" if theme_style == "flat" else "",
                "icon": " ", "raw_tmpl": "$path",
                "options": {},
            })

        if "git_branch" not in all_parsed_names and not has_block_diamonds:
            dir_idx = next((i for i, p in enumerate(parsed_l1_left) if p["mod_name"] == "directory"), -1)
            target_idx = dir_idx + 1 if dir_idx >= 0 else len(parsed_l1_left)
            parsed_l1_left.insert(target_idx, {
                "mod_name": "git_branch", "var_name": "$git_branch",
                "fg": "#addb67" if theme_style == "flat" else "#011627",
                "bg": None if theme_style == "flat" else "#addb67",
                "leading": "" if theme_style == "flat" else "",
                "trailing": "" if theme_style == "flat" else "",
                "icon": " ", "raw_tmpl": "$branch",
                "options": {},
            })

        # Build Line 1 Left modules
        self.parsed_l1_left = parsed_l1_left
        line1_left_mods = []
        for i, m in enumerate(parsed_l1_left):
            prev_m = parsed_l1_left[i - 1] if i > 0 else None
            next_m = parsed_l1_left[i + 1] if i + 1 < len(parsed_l1_left) else None
            self.build_left_module(m, theme_style, next_mod=next_m, prev_mod=prev_m, is_first_on_line=(i == 0))
            if m["var_name"] not in line1_left_mods:
                line1_left_mods.append(m["var_name"])
                if m["mod_name"] == "username" and m.get("has_host") and "$hostname" not in line1_left_mods:
                    line1_left_mods.append("$hostname")
                if m["mod_name"] == "git_branch" and "$git_status" not in line1_left_mods:
                    line1_left_mods.append("$git_status")

        # Parse Line 1 Right segments
        parsed_l1_right = []
        for s in line1_right:
            mod = self.parse_segment(s)
            if mod:
                parsed_l1_right.append(mod)

        # Deduplicate right-side modules by mod_name
        seen_mods = set()
        deduped_right = []
        for p in parsed_l1_right:
            if p["mod_name"] not in seen_mods:
                seen_mods.add(p["mod_name"])
                deduped_right.append(p)
        parsed_l1_right = deduped_right

        # Forward delimiters from leading of next module to trailing of current module
        for i in range(len(parsed_l1_right) - 1):
            curr_m = parsed_l1_right[i]
            next_m = parsed_l1_right[i + 1]
            if next_m.get("leading") in ("\u250b", "┆", "┋", "|", "│"):
                curr_m["trailing"] = next_m["leading"]
                next_m["leading"] = ""

        # Inject developer runtimes if appropriate (and not already present on left)
        has_left_runtime = any(p["mod_name"] in [r[0] for r in STANDARD_DEVELOPER_RUNTIMES] for p in parsed_l1_left)
        if should_inject_runtimes and not has_left_runtime and not (is_single_line and theme_style == "powerline"):
            has_runtime = any(p["mod_name"] in [r[0] for r in STANDARD_DEVELOPER_RUNTIMES] for p in parsed_l1_right)
            if not has_runtime:
                ins_idx = len(parsed_l1_right)
                for i, p in enumerate(parsed_l1_right):
                    if p["mod_name"] in ("cmd_duration", "time"):
                        ins_idx = i
                        break
                injected = []
                for m_name, v_name, ic, fg in STANDARD_DEVELOPER_RUNTIMES:
                    if m_name not in seen_mods:
                        seen_mods.add(m_name)
                        injected.append({
                            "mod_name": m_name, "var_name": v_name,
                            "fg": fg, "bg": None if theme_style == "flat" else "#0b2942",
                            "leading": "", "trailing": "",
                            "icon": ic, "raw_tmpl": "$version",
                            "options": {},
                        })
                parsed_l1_right[ins_idx:ins_idx] = injected

        # Determine Right Style: flat, powerline (prev_bg), ribbon (unified), or pills
        if theme_style == "flat":
            right_style = "flat"
        elif self.use_pills or has_pill_diamonds:
            right_style = "pills"
        elif theme_style == "powerline":
            right_style = "powerline"
        else:
            right_style = "ribbon"

        # Deduce ribbon background color for unified ribbon if applicable
        ribbon_bg = self.ribbon_bg_override
        if not ribbon_bg and right_style == "ribbon":
            time_seg = next((p for p in parsed_l1_right if p["mod_name"] == "time"), None)
            if time_seg and time_seg.get("bg"):
                ribbon_bg = time_seg["bg"]

            if not ribbon_bg:
                user_seg = next((p for p in parsed_l1_right if p["mod_name"] == "username"), None)
                if user_seg and user_seg.get("bg"):
                    ribbon_bg = user_seg["bg"]

            if not ribbon_bg:
                bgs = [p["bg"] for p in parsed_l1_right if p.get("bg")]
                if bgs:
                    ribbon_bg = Counter(bgs).most_common(1)[0][0]

            if not ribbon_bg:
                for k in ("surface", "background", "mantle", "bg", "crust", "panel"):
                    if k in self.palette:
                        ribbon_bg = self.resolve_color(f"p:{k}")
                        if ribbon_bg:
                            break

            if not ribbon_bg:
                ribbon_bg = "#0b2942"

        line1_right_mods = []
        for m in parsed_l1_right:
            self.build_right_module(m, right_style, ribbon_bg)
            if m["var_name"] not in line1_right_mods:
                line1_right_mods.append(m["var_name"])
                if m["mod_name"] == "username" and m.get("has_host") and "$hostname" not in line1_right_mods:
                    line1_right_mods.append("$hostname")
                if m["mod_name"] == "git_branch" and "$git_status" not in line1_right_mods:
                    line1_right_mods.append("$git_status")

        # Step 5: Process Subsequent Lines (Line 2+)
        subsequent_line_mods: List[List[str]] = []
        for pl in prompt_lines[1:]:
            curr_sub_mods = []
            parsed_pl_left = []
            for s in pl["left"]:
                mod = self.parse_segment(s)
                if mod:
                    if parsed_pl_left and parsed_pl_left[-1]["mod_name"] == mod["mod_name"]:
                        if parsed_pl_left[-1].get("leading") and not mod.get("leading"):
                            mod["leading"] = parsed_pl_left[-1]["leading"]
                        parsed_pl_left[-1] = mod
                    else:
                        parsed_pl_left.append(mod)
            for i, mod in enumerate(parsed_pl_left):
                prev_m = parsed_pl_left[i - 1] if i > 0 else None
                next_m = parsed_pl_left[i + 1] if i + 1 < len(parsed_pl_left) else None
                if mod.get("mod_name") != "connector":
                    self.build_left_module(mod, theme_style, next_mod=next_m, prev_mod=prev_m, is_first_on_line=(i == 0))
                if mod["var_name"] not in curr_sub_mods:
                    curr_sub_mods.append(mod["var_name"])
                    if mod["mod_name"] == "username" and mod.get("has_host") and "$hostname" not in curr_sub_mods:
                        curr_sub_mods.append("$hostname")
                    if mod["mod_name"] == "git_branch" and "$git_status" not in curr_sub_mods:
                        curr_sub_mods.append("$git_status")
            has_actual_modules = any(m.startswith("$") for m in curr_sub_mods)
            if curr_sub_mods and has_actual_modules:
                subsequent_line_mods.append(curr_sub_mods)

        has_rprompt = any(b.get("type") == "rprompt" for b in blocks)

        # Attach $character (and $username if pill prompt user) to the last line
        if is_single_line:
            if has_rprompt or theme_style == "powerline":
                if has_pill_prompt_user and "$username" not in line1_left_mods:
                    line1_left_mods.append("$username")
                if "$character" not in line1_left_mods:
                    line1_left_mods.append("$character")
            else:
                if has_pill_prompt_user and "$username" not in line1_right_mods and "$username" not in line1_left_mods:
                    line1_right_mods.append("$username")
                if "$character" not in line1_right_mods:
                    line1_right_mods.append("$character")
        else:
            if not subsequent_line_mods or len(subsequent_line_mods) < (len(prompt_lines) - 1):
                subsequent_line_mods.append([])
            if has_pill_prompt_user and "$username" not in subsequent_line_mods[-1]:
                subsequent_line_mods[-1].append("$username")
            subsequent_line_mods[-1].append("$character")

        # Configure character module for single-line powerline
        if is_single_line and theme_style == "powerline":
            last_left_mod = parsed_l1_left[-1] if parsed_l1_left else None
            last_has_closed = bool(
                last_left_mod and (
                    last_left_mod.get("trailing_diamond") or
                    "<transparent" in last_left_mod.get("trailing", "")
                )
            )
            dir_mod = next((p for p in parsed_l1_left if p["mod_name"] == "directory"), None)
            git_mod = next((p for p in parsed_l1_left if p["mod_name"] == "git_branch"), None)
            is_same_bg_powerline = bool(dir_mod and git_mod and dir_mod.get("bg") == git_mod.get("bg"))
            if is_same_bg_powerline or last_has_closed:
                self.modules["character"] = {
                    "format": "$symbol",
                    "success_symbol": "",
                    "error_symbol": "",
                }
            else:
                pwr_sym = getattr(self, "powerline_symbol", "\ue0b0")
                close_glyph = "\ue0b4" if (pwr_sym in ("\ue0b4", "") or getattr(self, "powerline_symbol", "") in ("\ue0b4", "")) else ("\ue0c4" if pwr_sym == "\ue0c4" else "\ue0b0")
                self.modules["character"] = {
                    "format": "$symbol",
                    "success_symbol": f"[{close_glyph}](fg:prev_bg) ",
                    "error_symbol": f"[{close_glyph}](fg:prev_bg) ",
                }
        elif not is_single_line and theme_style == "powerline":
            last_line_segs = prompt_lines[-1]["left"] if prompt_lines else []
            last_seg = last_line_segs[-1] if last_line_segs else None
            char_is_plain = getattr(self, "char_is_plain", False)
            if last_seg and (last_seg.get("background") or last_seg.get("trailing_diamond") == "\ue0b0") and not char_is_plain:
                sym_fmt = self.modules.get("character", {}).get("format", "$symbol")
                if "" not in sym_fmt:
                    if "character" not in self.modules:
                        self.modules["character"] = {}
                    self.modules["character"]["format"] = f"[](fg:prev_bg) {sym_fmt}"

        return self.render_toml(
            line1_left_mods=line1_left_mods,
            line1_right_mods=line1_right_mods,
            subsequent_lines=subsequent_line_mods,
            is_single_line=is_single_line,
            right_style=right_style,
            ribbon_bg=ribbon_bg,
            has_rprompt=has_rprompt,
        )

    def parse_segment(self, s: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        res = self._parse_segment_raw(s)
        if res:
            res["trailing_diamond"] = s.get("trailing_diamond", "")
            res["leading_diamond"] = s.get("leading_diamond", "")
            res["seg_style"] = s.get("style", "")
            tmpl = s.get("template", "")
            m_frame = re.search(r"<([#a-zA-Z0-9_\-]+)>([┏┖┗\u250f\u2514\u2516])?\[</>", tmpl)
            bracket_color = None
            box_char = ""
            if m_frame:
                bracket_color = self.resolve_color(m_frame.group(1))
                box_char = m_frame.group(2) or ""
            elif any(c in tmpl for c in ("┏", "\u250f", "┗", "┖", "\u2514", "\u2516")):
                for c in ("┏", "\u250f", "┗", "┖", "\u2514", "\u2516"):
                    if c in tmpl:
                        box_char = c
                        break
                m_col = re.search(r"<([#a-zA-Z0-9_\-]+)>", tmpl)
                if m_col:
                    bracket_color = self.resolve_color(m_col.group(1))
            if bracket_color or box_char:
                res["bracket_fg"] = bracket_color
                res["box_char"] = box_char
                res["is_bracketed"] = True
        return res

    def _parse_segment_raw(self, s: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        stype = s.get("type", "")
        if stype == "block_connector":
            return {
                "mod_name": "connector", "var_name": s.get("markup", ""),
                "fg": None, "bg": None,
                "leading": "", "trailing": "",
                "icon": "", "raw_tmpl": "",
                "options": {},
                "template": "",
                "is_bracketed": False,
            }

        fg, bg = self.get_seg_colors(s)
        tmpl = s.get("template", "")
        options = s.get("options") or s.get("properties") or {}
        lead = s.get("leading_diamond", "")
        trail = s.get("trailing_diamond", "") or s.get("powerline_symbol", "")
        if not lead and "<transparent" in tmpl:
            m_lead = re.search(r"<transparent[^>]*>([\ue0b0\ue0b2])</>", tmpl)
            if m_lead:
                lead = m_lead.group(0)
        is_bracketed = (tmpl.strip().startswith("[") and tmpl.strip().endswith("]")) or "<#CB4B16>[" in tmpl

        extra_text = ""
        if stype == "session":
            m = re.search(r"\{\{\s*\.UserName\s*\}\}(.*?)\{\{\s*\.HostName\s*\}\}", tmpl)
            if m:
                extra_text = m.group(1)
            elif ".HostName" in tmpl:
                extra_text = "@"
        elif stype == "executiontime":
            if "\ue601" in tmpl:
                options["icon"] = " "
            elif "\ueba2" in tmpl:
                options["icon"] = " "

        if stype == "os":
            win_sym = options.get("windows") or ""
            return {
                "mod_name": "os", "var_name": "$os",
                "fg": fg or "#011627", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": win_sym, "raw_tmpl": "$symbol",
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype == "root":
            sym = "⚡ "
            if "\uf292" in tmpl or "#" in tmpl:
                sym = " " if bg else ""
            elif "\u26a1" in tmpl or "⚡" in tmpl or "" in tmpl:
                sym = " "
            return {
                "mod_name": "sudo", "var_name": "$sudo",
                "fg": fg or "#ffeb95", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": sym, "raw_tmpl": "",
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype == "path":
            has_icon = any(x in tmpl for x in ("\uf07c", "\ue5ff", "\uf115", ".Icon"))
            icon = ""
            if has_icon:
                icon = " " if "\ue5ff" in tmpl else " "
            has_trailing_slash = tmpl.strip().endswith("/") or ".Path }}/" in tmpl
            return {
                "mod_name": "directory", "var_name": "$directory",
                "fg": fg or ("#FEF5ED" if self.has_top_connector else "#82AAFF"), "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": icon, "raw_tmpl": "$path",
                "has_trailing_slash": has_trailing_slash,
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype == "git":
            raw_b = options.get("branch_icon", "")
            b_icon = " "
            if "\ue725" in raw_b or "\ue725" in tmpl:
                b_icon = " "
            elif "\ue0a0" in raw_b or "\ue0a0" in tmpl:
                b_icon = " "
            prefix = ""
            if "on" in tmpl:
                m_col = re.search(r"<([#a-zA-Z0-9_\-]+)>on</>", tmpl)
                p_col = m_col.group(1) if m_col else "#ffffff"
                prefix = f"[on ](fg:{p_col})"
            return {
                "mod_name": "git_branch", "var_name": "$git_branch",
                "fg": fg or "#addb67", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": b_icon, "raw_tmpl": "$branch",
                "prefix": prefix,
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype == "session":
            has_host = "{{ .HostName }}" in tmpl or ".HostName" in tmpl
            has_icon = any(x in tmpl for x in ("\uf007", "\uf2bd", "\ue712", "\ueb99", ".Icon"))
            icon = " " if "\ueb99" in tmpl else (" " if has_icon else "")
            return {
                "mod_name": "username", "var_name": "$username",
                "fg": fg or "#43CCEA", "bg": bg,
                "leading": lead, "trailing": trail,
                "extra_text": extra_text,
                "has_host": has_host,
                "icon": icon, "raw_tmpl": "$user",
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype == "status":
            return {
                "mod_name": "status", "var_name": "$status",
                "fg": fg or "#ffffff", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": "❌" if "❌" in tmpl else "",
                "raw_tmpl": "$status",
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype == "executiontime":
            icon = options.get("icon") or ""
            if not icon:
                if "\ue601" in tmpl:
                    icon = " "
                elif "\ueba2" in tmpl:
                    icon = " "
                elif any(c in tmpl for c in ("\uf017", "", "\uf252", "\uf253", "\uf251", "\uf250")):
                    icon = " "
            return {
                "mod_name": "cmd_duration", "var_name": "$cmd_duration",
                "fg": fg or "#ECC48D", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": icon, "raw_tmpl": "$duration",
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype == "shell":
            return {
                "mod_name": "shell", "var_name": "$shell",
                "fg": fg or "#011627", "bg": bg or "#FEF5ED",
                "leading": lead, "trailing": trail,
                "icon": " ", "raw_tmpl": "$indicator",
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype == "text":
            if any(c in tmpl for c in ("\u256d", "╭")):
                col = fg or "#FEF5ED"
                return {
                    "mod_name": "connector", "var_name": f"[{tmpl.strip()}](fg:{col}) ",
                    "fg": col, "bg": None,
                    "leading": lead, "trailing": trail,
                    "icon": "", "raw_tmpl": tmpl,
                    "options": options,
                    "template": tmpl,
                    "is_bracketed": is_bracketed,
                }
            return None
        elif stype == "time":
            has_icon = any(x in tmpl for x in ("\uf017", "\ue383", "\uf073", ".Icon"))
            icon = " " if "\uf073" in tmpl else (" " if has_icon else "")
            if "\u2665" in tmpl or "♥" in tmpl:
                icon = "♡ "
            return {
                "mod_name": "time", "var_name": "$time",
                "fg": fg or ("#FEF5ED" if self.has_top_connector else "#82AAFF"), "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": icon, "raw_tmpl": "$time",
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype in ("battery",):
            return {
                "mod_name": "battery", "var_name": "$battery",
                "fg": fg or "#A6E3A1", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": "󰁹 ", "raw_tmpl": "$percentage",
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype in ("sysinfo", "memory"):
            has_icon = any(c in tmpl for c in ("\ue266", "󰍛", ""))
            icon = "󰍛 " if has_icon else ""

            prefix = ""
            color_tags = re.findall(r"<([#a-zA-Z0-9_\-]+)>([^<]*)</>", tmpl)
            if color_tags:
                prefix = "".join(f"[{txt}](fg:{col})" for col, txt in color_tags if any(k in txt for k in ("|", "MEM:", "RAM:", "MEM", "RAM", "\ue266")))

            raw_tmpl = "$ram_pct"
            if "RAM:" in tmpl or "TotalMemory" in tmpl:
                if "PercentUsed" in tmpl or "%" in tmpl:
                    if prefix:
                        raw_tmpl = "$ram_pct ($ram)"
                    else:
                        raw_tmpl = "MEM: $ram_pct | $ram"
                else:
                    if prefix:
                        raw_tmpl = " $ram"
                    else:
                        raw_tmpl = "RAM:$ram"
            elif "MEM:" in tmpl:
                if prefix:
                    raw_tmpl = " $ram_pct"
                else:
                    raw_tmpl = "MEM: $ram_pct"

            return {
                "mod_name": "memory_usage", "var_name": "$memory_usage",
                "fg": fg or "#C792EA", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": icon, "raw_tmpl": raw_tmpl,
                "prefix": prefix,
                "options": options,
                "template": tmpl,
                "is_bracketed": is_bracketed,
            }
        elif stype in RUNTIME_MAPPINGS:
            m_name, v_name, ic, def_fg = RUNTIME_MAPPINGS[stype]
            if "\ue781" in tmpl or "\ue718" in tmpl:
                ic = " "
            prefix = ""
            if "via" in tmpl:
                m_col = re.search(r"<([#a-zA-Z0-9_\-]+)>via</>", tmpl)
                p_col = m_col.group(1) if m_col else "#ffffff"
                prefix = f"[via ](fg:{p_col})"
            return {
                "mod_name": m_name, "var_name": v_name,
                "fg": fg or def_fg, "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": ic, "raw_tmpl": "$version",
                "prefix": prefix,
                "options": options,
                "template": tmpl,
            }

        return None

    def build_left_module(self, curr: Dict[str, Any], style: str, next_mod: Optional[Dict[str, Any]] = None, prev_mod: Optional[Dict[str, Any]] = None, is_first_on_line: bool = False) -> None:
        mod_name = curr["mod_name"]
        if mod_name == "connector":
            return

        bg = curr["bg"]
        fg = curr["fg"] or "#ffffff"
        icon = curr["icon"]

        # Case 0: Bracket frame style (like darkblood)
        if style == "bracket_frame" or curr.get("bracket_fg"):
            b_fg = curr.get("bracket_fg") or getattr(self, "bracket_fg", "#CB4B16")
            box_dir_prefix = f"[┗\\[](fg:{b_fg})"

            if mod_name == "username":
                self.modules["username"] = {
                    "show_always": True,
                    "format": f"[\\[](fg:{b_fg})[$user](fg:{fg})[\\]](fg:{b_fg})",
                }
            elif mod_name == "git_branch":
                self.modules["git_branch"] = {
                    "symbol": "",
                    "format": f"[\\[](fg:{b_fg})[$symbol$branch](fg:{fg})[\\]](fg:{b_fg})",
                }
                self.modules["git_status"] = {
                    "disabled": True,
                }
            elif mod_name == "sudo":
                self.modules["sudo"] = {
                    "disabled": False,
                    "style": f"fg:{fg}",
                    "format": f"[\\[](fg:{b_fg})[⚡](fg:{fg})[\\]](fg:{b_fg})",
                }
            elif mod_name == "status":
                self.modules["status"] = {
                    "disabled": False,
                    "format": f"[\\[x](fg:{b_fg})[$symbol](fg:{fg})[\\]](fg:{b_fg})",
                    "success_symbol": "0",
                    "symbol": "$status",
                }
            elif mod_name == "directory":
                self.modules["directory"] = {
                    "format": f"{box_dir_prefix}[$path](fg:{fg})[\\]](fg:{b_fg})",
                    "truncation_length": 3,
                    "truncation_symbol": "…/",
                }
            return

        # Case 1: Flat style or segment without background
        if style == "flat" or not bg:
            if curr.get("is_bracketed"):
                left_b = rf"[\[](bold {fg})"
                right_b = rf"[\]](bold {fg})"

                if mod_name == "directory":
                    icon_str = f"[ {icon}](bold #ffffff)" if icon else ""
                    path_fg = "#98bfad" if "#98bfad" in curr.get("template", "") else fg
                    path_var = "$path/" if curr.get("has_trailing_slash") else "$path"
                    self.modules["directory"] = {
                        "format": f"{left_b}{icon_str}[{path_var}](bold {path_fg}){right_b}",
                        "truncation_length": 3,
                        "truncation_symbol": "…/",
                    }
                elif mod_name == "git_branch":
                    icon_str = f"[ {icon}](bold #ffffff)" if icon else ""
                    self.modules["git_branch"] = {
                        "format": f"{left_b}{icon_str}[$branch](bold {fg})",
                    }
                    self.modules["git_status"] = {
                        "format": f"([$all_status$ahead_behind](bold {fg})){right_b}",
                        "modified": " ✎",
                        "staged": " ",
                        "stashed": " ",
                        "ahead": " ⇡${count}",
                        "behind": " ⇣${count}",
                        "diverged": " ⇕⇡${ahead_count}⇣${behind_count}",
                    }
                elif mod_name == "username":
                    user_icon = f"[ {icon}](bold #ffffff)" if icon else ""
                    if curr.get("has_host"):
                        host_icon = " " if "\uf108" in curr.get("template", "") else ""
                        self.modules["username"] = {
                            "format": f"{left_b}{user_icon}[$user ](bold {fg})",
                            "show_always": True,
                        }
                        self.modules["hostname"] = {
                            "format": f"[:: ](bold #ffffff)[{host_icon}](bold #ffffff)[$hostname](bold {fg}){right_b}",
                            "ssh_only": False,
                        }
                    else:
                        self.modules["username"] = {
                            "format": f"{left_b}{user_icon}[$user](bold {fg}){right_b}",
                            "show_always": True,
                        }
                elif mod_name == "time":
                    raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                    icon_str = f"[ {icon}](bold #ffffff)" if icon else ""
                    self.modules["time"] = {
                        "format": f"{left_b}{icon_str}[$time](bold {fg}){right_b}",
                        "disabled": False,
                        "time_format": convert_go_date_format(raw_t),
                    }
                elif mod_name == "cmd_duration":
                    icon_str = f"[ {icon}](bold #ffffff)" if icon else ""
                    self.modules["cmd_duration"] = {
                        "format": f"{left_b}{icon_str}[$duration](bold {fg}){right_b}",
                        "min_time": 0,
                        "show_milliseconds": True,
                    }
                elif mod_name == "memory_usage":
                    icon_str = f"[ {icon}](bold #ffffff)" if icon else ""
                    raw_tmpl = curr.get("raw_tmpl") or "RAM: $ram"
                    if "RAM:" in curr.get("template", "") or "RAM" in curr.get("template", ""):
                        raw_tmpl = "RAM: $ram"
                    elif not raw_tmpl.startswith(" ") and not raw_tmpl.startswith("RAM:"):
                        raw_tmpl = f" {raw_tmpl}"
                    self.modules["memory_usage"] = {
                        "format": f"{left_b}{icon_str}[{raw_tmpl}](bold {fg}){right_b}",
                        "disabled": False,
                        "threshold": -1,
                        "symbol": "",
                        "style": f"bold {fg}",
                    }
                elif mod_name == "battery":
                    icon_str = f"{icon}" if icon else ""
                    self.modules["battery"] = {
                        "format": f"{left_b}[{icon_str}$percentage](bold {fg}){right_b}",
                        "disabled": False,
                        "style": f"bold {fg}",
                    }
                return

            lead_span = parse_omp_markup(curr.get("leading"), fg)
            trail_span = parse_omp_markup(curr.get("trailing"), fg)
            extra_span = parse_omp_markup(curr.get("extra_text"), fg)

            if mod_name == "directory":
                fg_col = fg or "#FEF5ED"
                icon_str = f"{icon}" if icon else ""
                path_var = "$path/" if curr.get("has_trailing_slash") else "$path"
                self.modules["directory"] = {
                    "format": f"{lead_span}[{icon_str}{path_var} ](fg:{fg_col}){trail_span} ",
                    "truncation_length": 3,
                    "truncation_symbol": "…/",
                }
            elif mod_name == "git_branch":
                prefix = curr.get("prefix", "")
                self.modules["git_branch"] = {
                    "format": f"{prefix}[{icon}$branch](bold {fg})",
                }
                self.modules["git_status"] = {
                    "format": f"([$all_status$ahead_behind](bold {fg})) ",
                    "modified": " ✎",
                    "staged": " ",
                    "stashed": " ",
                    "ahead": " ⇡${count}",
                    "behind": " ⇣${count}",
                    "diverged": " ⇕⇡${ahead_count}⇣${behind_count}",
                }
            elif mod_name == "username":
                extra_txt = curr.get("extra_text", "")
                icon_str = f"{icon}" if icon else ""
                if curr.get("has_host"):
                    self.modules["username"] = {
                        "format": f"{lead_span}[{icon_str}$user ](bold {fg})",
                        "show_always": True,
                    }
                    self.modules["hostname"] = {
                        "format": f"[@$hostname ](bold {fg}) ",
                        "ssh_only": True,
                    }
                else:
                    if "<" in extra_txt:
                        extra_span = " " + parse_omp_markup(extra_txt, fg)
                        user_str = "$user"
                    else:
                        extra_span = ""
                        user_str = f"$user{extra_txt}" if extra_txt else "$user"
                    self.modules["username"] = {
                        "format": f"{lead_span}[{icon_str}{user_str} ](bold {fg}){extra_span}",
                        "show_always": True,
                    }
            elif mod_name == "time":
                raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                suffix = " |" if "|" in curr.get("template", "") else ""
                icon_str = f"{icon}" if icon else ""
                fg_col = fg or "#FEF5ED"
                self.modules["time"] = {
                    "format": f"[{icon_str}$time{suffix}](fg:{fg_col}) ",
                    "disabled": False,
                    "time_format": convert_go_date_format(raw_t),
                }
            elif mod_name == "cmd_duration":
                self.modules["cmd_duration"] = {
                    "format": f"[ $duration {icon}](bold {fg}) ",
                    "min_time": 2000,
                }
            elif mod_name == "os":
                lead_str = parse_omp_markup(curr.get("leading"), fg)
                self.modules["os"] = {
                    "disabled": False,
                    "style": f"bold {fg}",
                    "format": f"{lead_str}[ $symbol ]($style) ",
                }
                self.modules["os.symbols"] = {
                    "Windows": "",
                    "Ubuntu": "",
                    "Macos": "",
                    "Linux": "",
                }
            elif mod_name == "sudo":
                fg_col = fg or "#FEF5ED"
                self.modules["sudo"] = {
                    "style": f"bold {fg_col}",
                    "format": f"[# ](fg:{fg_col}) " if ("#" in curr.get("template", "") or "\uf292" in curr.get("template", "")) else f"[ {icon}]($style) ",
                    "allow_windows": True,
                    "disabled": False,
                }
            elif mod_name == "status":
                sym = curr.get("icon") or "❌"
                self.modules["status"] = {
                    "format": f"[$symbol ](fg:{fg})",
                    "symbol": sym,
                    "disabled": False,
                }
            elif mod_name == "memory_usage":
                raw_tmpl = curr.get("raw_tmpl", "$ram_pct")
                prefix = curr.get("prefix", "")
                self.modules["memory_usage"] = {
                    "disabled": False,
                    "threshold": -1,
                    "symbol": "",
                    "style": f"bold {fg}",
                    "format": f"{prefix}[{icon}{raw_tmpl} ]($style)",
                }
            elif mod_name == "battery":
                self.modules["battery"] = {
                    "disabled": False,
                    "format": f"[{icon}$percentage ](bold {fg}) ",
                }
            elif mod_name in RUNTIME_MAPPINGS or mod_name in [r[0] for r in STANDARD_DEVELOPER_RUNTIMES]:
                prefix = curr.get("prefix", "")
                self.modules[mod_name] = {
                    "format": f"{prefix}[{icon}$version ](bold {fg}) ",
                }
            return

        # Case 2: Dual-Capsule style
        if style == "capsule":
            lead_bracket = "╭─" if (self.has_top_connector and "os" not in self.modules) else ""
            if mod_name == "os":
                self.modules["os"] = {
                    "disabled": False,
                    "style": f"fg:{fg} bg:{bg}",
                    "format": f"[{lead_bracket}](fg:{bg})[ $symbol ]($style)[](fg:{bg}) ",
                }
                self.modules["os.symbols"] = {
                    "Windows": "",
                    "Ubuntu": "",
                    "Macos": "",
                    "Linux": "",
                }
            elif mod_name == "sudo":
                self.modules["sudo"] = {
                    "style": f"fg:{fg} bg:{bg}",
                    "format": f"[](fg:{bg})[ {icon}]($style)[](fg:{bg}) ",
                    "disabled": False,
                }
            elif mod_name == "directory":
                icon_str = f" {icon}" if icon else " "
                self.modules["directory"] = {
                    "format": f"[{lead_bracket}](fg:{bg})[{icon_str}$path ](fg:{fg} bg:{bg})[](fg:{bg}) ",
                    "truncation_length": 3,
                    "truncation_symbol": "…/",
                }
            elif mod_name == "git_branch":
                icon_str = f" {icon}" if icon else " "
                self.modules["git_branch"] = {
                    "format": f"[](fg:{bg})[{icon_str}$branch ](fg:{fg} bg:{bg})",
                }
                self.modules["git_status"] = {
                    "format": f"([$all_status$ahead_behind ](fg:{fg} bg:{bg}))[](fg:{bg}) ",
                    "modified": " ✎",
                    "staged": " ",
                    "stashed": " ",
                    "ahead": " ⇡${count}",
                    "behind": " ⇣${count}",
                    "diverged": " ⇕⇡${ahead_count}⇣${behind_count}",
                }
            elif mod_name == "username":
                icon_str = f" {icon}" if icon else " "
                self.modules["username"] = {
                    "format": f"[](fg:{bg})[{icon_str}$user ](fg:{fg} bg:{bg})[](fg:{bg}) ",
                    "show_always": True,
                }
            elif mod_name == "cmd_duration":
                icon_str = f" {icon}" if icon else " "
                thresh = curr.get("options", {}).get("threshold", 0)
                self.modules["cmd_duration"] = {
                    "format": f"[](fg:{bg})[{icon_str}$duration ](fg:{fg} bg:{bg})[](fg:{bg}) ",
                    "min_time": thresh,
                }
            elif mod_name == "time":
                raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                icon_str = f" {icon}" if icon else " "
                self.modules["time"] = {
                    "format": f"[](fg:{bg})[{icon_str}$time ](fg:{fg} bg:{bg})[](fg:{bg}) ",
                    "disabled": False,
                    "time_format": convert_go_date_format(raw_t),
                }
            elif mod_name == "memory_usage":
                icon_str = f" {icon}" if icon else " "
                raw_t = curr.get("raw_tmpl", "$ram_pct")
                self.modules["memory_usage"] = {
                    "disabled": False,
                    "threshold": -1,
                    "symbol": "",
                    "style": f"fg:{fg} bg:{bg}",
                    "format": f"[{lead_bracket}](fg:{bg})[{icon_str}{raw_t} ](fg:{fg} bg:{bg})[](fg:{bg}) ",
                }
            elif mod_name == "battery":
                icon_str = f" {icon}" if icon else " "
                self.modules["battery"] = {
                    "disabled": False,
                    "format": f"[{lead_bracket}](fg:{bg})[{icon_str}$percentage ](fg:{fg} bg:{bg})[](fg:{bg}) ",
                }
            else:
                icon_str = f" {icon}" if icon else " "
                raw_t = curr.get("raw_tmpl", "")
                self.modules[mod_name] = {
                    "format": f"[{lead_bracket}](fg:{bg})[{icon_str}{raw_t} ](fg:{fg} bg:{bg})[](fg:{bg}) ",
                }
            return

        # Case 3: Powerline chevron style
        if style == "powerline":
            l1_mods = getattr(self, "parsed_l1_left", [])
            is_first = is_first_on_line or bool(l1_mods and curr == l1_mods[0])

            next_bg = next_mod.get("bg") if next_mod else None
            connects_to_next = bool(
                bg and next_bg and
                not curr.get("trailing_diamond") and
                "<transparent" not in curr.get("trailing", "") and
                "<transparent" not in (next_mod.get("leading", "") if next_mod else "") and
                curr.get("trailing") not in ("\ue0b4", "\ue0c0", "\ue0b2") and
                (next_mod.get("leading") not in ("\ue0b2", "\ue0b6") if next_mod else True)
            )

            next_has_inward = bool(
                next_mod and (
                    "<transparent" in next_mod.get("leading", "") or
                    (curr.get("trailing_diamond") == "\ue0b0" and not next_mod.get("leading"))
                )
            )

            def format_dia_lead(c: Dict[str, Any], fallback_lead: str = "") -> str:
                ld = c.get("leading", "")
                c_bg = c.get("bg")
                if not ld or not c_bg:
                    return fallback_lead
                if "<transparent" in ld:
                    if "\ue0b0" in ld:
                        return f"[](fg:{c_bg} inverted)"
                    elif "\ue0b2" in ld:
                        return f"[](fg:{c_bg} inverted)"
                glyph = re.sub(r"<[^>]+>", "", ld).strip()
                if glyph:
                    return f"[{glyph}](fg:{c_bg})"
                return fallback_lead

            def format_dia_trail(c: Dict[str, Any], connects: bool = False, default_close: str = "") -> str:
                tr = c.get("trailing", "")
                c_bg = c.get("bg")
                if not c_bg:
                    return ""
                if "<transparent" in tr:
                    if "\ue0b2" in tr:
                        return f"[](fg:{c_bg} inverted) "
                    elif "\ue0b0" in tr:
                        return f"[](fg:{c_bg} inverted) "
                if connects:
                    return ""
                sp = "" if next_has_inward else " "
                if tr:
                    glyph = re.sub(r"<[^>]+>", "", tr).strip()
                    if glyph:
                        return f"[{glyph}](fg:{c_bg}){sp}"
                return default_close

            if is_first:
                lead_chevron = ""
            elif prev_mod and prev_mod.get("trailing_diamond") == "\ue0b0" and not curr.get("leading"):
                lead_chevron = f"[](fg:{bg} inverted)"
            elif prev_mod and prev_mod.get("bg") and prev_mod.get("bg") == bg:
                lead_chevron = f"[ ](fg:{fg} bg:{bg})"
            else:
                pwr_sym = getattr(self, "powerline_symbol", "\ue0b0")
                if pwr_sym == "\ue0b4":
                    lead_chevron = f"[](fg:prev_bg bg:{bg})"
                elif pwr_sym in ("\ue0c4", "\ue0c5"):
                    lead_chevron = f"[](fg:prev_bg bg:{bg})"
                elif pwr_sym == "":
                    lead_chevron = ""
                else:
                    lead_chevron = f"[{pwr_sym}](fg:prev_bg bg:{bg})"

            if mod_name == "os":
                tmpl = curr.get("template", "")
                os_divider = f"[ ](fg:{fg} bg:{bg})" if "\ue0b1" in tmpl else ""
                if not bg:
                    self.modules["os"] = {
                        "disabled": False,
                        "style": f"fg:{fg}",
                        "format": f"[ $symbol ]($style) ",
                    }
                else:
                    lead_str = format_dia_lead(curr, "")
                    pwr_sym = getattr(self, "powerline_symbol", "\ue0b0")
                    if next_mod and next_mod.get("bg") == bg:
                        trail_str = ""
                    elif pwr_sym in ("\ue0b4", "") and next_mod and next_mod.get("bg"):
                        trail_str = ""
                    else:
                        trail_str = format_dia_trail(curr, connects=connects_to_next)
                    self.modules["os"] = {
                        "disabled": False,
                        "style": f"fg:{fg} bg:{bg}",
                        "format": f"{lead_str}[ $symbol ]($style){os_divider}{trail_str}",
                    }
                self.modules["os.symbols"] = {
                    "Windows": "󰕮",
                    "Ubuntu": "",
                    "Macos": "",
                    "Linux": "",
                }
            elif mod_name == "shell":
                lead_str = format_dia_lead(curr, lead_chevron)
                trail_str = format_dia_trail(curr, connects=connects_to_next)
                self.modules["shell"] = {
                    "disabled": False,
                    "powershell_indicator": "pwsh",
                    "bash_indicator": "bash",
                    "zsh_indicator": "zsh",
                    "style": f"fg:{fg} bg:{bg}",
                    "format": f"{lead_str}[  $indicator ]($style){trail_str}",
                }
            elif mod_name == "memory_usage":
                lead_str = format_dia_lead(curr, lead_chevron)
                trail_str = format_dia_trail(curr, connects=connects_to_next)
                raw_t = curr.get("raw_tmpl") or "RAM: $ram"
                icon_s = f"{curr['icon']} " if curr.get("icon") else "󰍛 "
                self.modules["memory_usage"] = {
                    "disabled": False,
                    "threshold": -1,
                    "style": f"fg:{fg} bg:{bg}",
                    "symbol": "󰍛",
                    "format": f"{lead_str}[ {icon_s}{raw_t} ]($style){trail_str}",
                }
            elif mod_name == "battery":
                lead_str = format_dia_lead(curr, lead_chevron)
                trail_str = format_dia_trail(curr, connects=connects_to_next)
                self.modules["battery"] = {
                    "disabled": False,
                    "format": f"{lead_str}[ 󰁹 $percentage ](fg:{fg} bg:{bg}){trail_str}",
                }
            elif mod_name == "sudo":
                pwr_sym = getattr(self, "powerline_symbol", "\ue0b0")
                if is_first and (curr.get("trailing") in ("\ue0c4", "\ue0c5", "\ue0c6") or pwr_sym == "\ue0c4"):
                    self.modules["sudo"] = {
                        "disabled": False,
                        "style": f"fg:{fg} bg:{bg}",
                        "format": f"[](fg:{bg})[ ⚡ ](fg:{fg} bg:{bg})[](fg:{bg}) ",
                    }
                elif bg:
                    lead_str = format_dia_lead(curr, lead_chevron)
                    trail_str = format_dia_trail(curr, connects=connects_to_next)
                    self.modules["sudo"] = {
                        "style": f"fg:{fg} bg:{bg}",
                        "format": f"{lead_str}[ ⚡ ]($style){trail_str}",
                        "disabled": False,
                    }
                else:
                    self.modules["sudo"] = {
                        "format": f"[# ](fg:{fg}) " if "#" in curr.get("template", "") else f"[ {icon}](fg:{fg}) ",
                        "disabled": False,
                    }
            elif mod_name == "username":
                if bg:
                    lead_str = format_dia_lead(curr, lead_chevron)
                    trail_str = format_dia_trail(curr, connects=connects_to_next)
                    pwr_sym = getattr(self, "powerline_symbol", "\ue0b0")
                    host_trail = "" if (pwr_sym in ("\ue0b4", "") and next_mod and next_mod.get("bg")) else trail_str
                    user_trail = "" if (pwr_sym in ("\ue0b4", "") and next_mod and next_mod.get("bg")) else trail_str
                    if curr.get("has_host"):
                        sep = curr.get("extra_text") or "@"
                        self.modules["username"] = {
                            "format": f"{lead_str}[ {icon}$user](fg:{fg} bg:{bg})",
                            "show_always": True,
                        }
                        self.modules["hostname"] = {
                            "format": f"[{sep}$hostname ](fg:{fg} bg:{bg}){host_trail}",
                            "ssh_only": False,
                        }
                    else:
                        self.modules["username"] = {
                            "format": f"{lead_str}[ {icon}$user ](fg:{fg} bg:{bg}){user_trail}",
                            "show_always": True,
                        }
                else:
                    self.modules["username"] = {
                        "format": f"[$user ](fg:{fg})",
                        "show_always": False,
                    }
            elif mod_name == "directory":
                icon_part = f"{icon}" if icon else ""
                lead_str = format_dia_lead(curr, lead_chevron)
                pwr_sym = getattr(self, "powerline_symbol", "\ue0b0")
                trail_str = "" if (pwr_sym in ("\ue0b4", "") and next_mod and next_mod.get("bg")) else format_dia_trail(curr, connects=connects_to_next)
                self.modules["directory"] = {
                    "format": f"{lead_str}[ {icon_part}$path ](fg:{fg} bg:{bg}){trail_str}",
                    "truncation_length": 3,
                    "truncation_symbol": "…/",
                }
            elif mod_name == "git_branch":
                icon_part = f"{icon}" if icon else ""
                dir_mod = next((p for p in l1_mods if p["mod_name"] == "directory"), None)
                same_bg = bool((prev_mod and prev_mod.get("bg") == bg) or (dir_mod and dir_mod.get("bg") == bg))
                lead_str = format_dia_lead(curr, lead_chevron)
                pwr_sym = getattr(self, "powerline_symbol", "\ue0b0")
                if pwr_sym in ("", "\ue0b4"):
                    def_close = ""
                elif pwr_sym in ("\ue0c4", "\ue0c5"):
                    def_close = f"[](fg:{bg}) " if not next_has_inward else f"[](fg:{bg})"
                else:
                    def_close = f"[](fg:{bg})" if next_has_inward else f"[](fg:{bg}) "
                if pwr_sym in ("\ue0b4", "") or (not next_mod and is_single_line):
                    trail_str = ""
                else:
                    trail_str = format_dia_trail(curr, connects=connects_to_next, default_close=def_close)

                if same_bg:
                    self.modules["git_branch"] = {
                        "format": f"[ {icon_part}$branch ](fg:{fg} bg:{bg})"
                    }
                    self.modules["git_status"] = {
                        "format": f"([$all_status$ahead_behind ](fg:{fg} bg:{bg})){trail_str}",
                        "modified": " ~${count}",
                        "staged": " +${count}",
                        "stashed": " *${count}",
                        "ahead": " ↑${count}",
                        "behind": " ↓${count}",
                        "diverged": " ↕↑${ahead_count}↓${behind_count}",
                        "deleted": " -${count}",
                    }
                else:
                    self.modules["git_branch"] = {
                        "format": f"{lead_str}[ {icon_part}$branch ](fg:{fg} bg:{bg})"
                    }
                    self.modules["git_status"] = {
                        "format": f"([$all_status$ahead_behind ](fg:{fg} bg:{bg})){trail_str}",
                        "modified": " ✎",
                        "staged": " ",
                        "stashed": " ",
                        "ahead": " ⇡${count}",
                        "behind": " ⇣${count}",
                        "diverged": " ⇕⇡${ahead_count}⇣${behind_count}",
                    }
            elif mod_name == "status":
                tmpl = curr.get("template", "")
                always_en = curr.get("options", {}).get("always_enabled", False)
                sym = curr.get("icon") or "❌"
                tmpl_icons = [c for c in tmpl if ord(c) > 127 and c not in ("\ue0b0", "\ue0b2", "\ue0b4", "\ue0b6", "\ue0b1", "\ue0b3", "\ue0c2")]
                if tmpl_icons:
                    sym = "".join(tmpl_icons).strip()
                if bg:
                    lead_str = format_dia_lead(curr, lead_chevron)
                    trail_str = format_dia_trail(curr, connects=connects_to_next)
                    status_dict = {
                        "format": f"{lead_str}[ $symbol ](fg:{fg} bg:{bg}){trail_str}",
                        "disabled": False,
                        "symbol": "❌",
                    }
                    if always_en or tmpl_icons:
                        status_dict["success_symbol"] = sym or "󰄬"
                    self.modules["status"] = status_dict
                else:
                    self.modules["status"] = {
                        "format": f"[$symbol ](fg:{fg})",
                        "symbol": sym,
                        "disabled": False,
                    }
            elif mod_name in RUNTIME_MAPPINGS or mod_name in [r[0] for r in STANDARD_DEVELOPER_RUNTIMES] or mod_name == "python":
                lead_str = format_dia_lead(curr, lead_chevron)
                trail_str = format_dia_trail(curr, connects=connects_to_next)
                tmpl = curr.get("template", "")
                raw_t = "$version"
                mod_icon = icon
                if mod_name == "azure":
                    raw_t = "$subscription"
                    if not mod_icon:
                        mod_icon = "󰠅 "
                elif mod_name == "terraform":
                    raw_t = "$workspace"
                    if not mod_icon:
                        mod_icon = "󱁢 "
                elif mod_name == "python":
                    if ".Venv" in tmpl:
                        raw_t = "${virtualenv} $version"
                    has_icon_in_tmpl = any(ord(c) > 127 for c in re.sub(r'\{\{[^}]*\}\}', '', tmpl))
                    if not has_icon_in_tmpl:
                        mod_icon = ""
                icon_str = f"{mod_icon} " if mod_icon and not mod_icon.endswith(" ") else (mod_icon or "")
                mod_dict = {
                    "format": f"{lead_str}[ {icon_str}{raw_t} ](fg:{fg} bg:{bg}){trail_str}"
                }
                if mod_name in ("azure", "terraform"):
                    mod_dict["disabled"] = False
                if mod_name == "python" and ".Full" in tmpl:
                    mod_dict["version_format"] = "${raw}"
                self.modules[mod_name] = mod_dict
            elif mod_name == "time":
                raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                lead_str = format_dia_lead(curr, lead_chevron)
                trail_str = format_dia_trail(curr, connects=connects_to_next)
                self.modules["time"] = {
                    "format": f"{lead_str}[ {icon}$time ](fg:{fg} bg:{bg}){trail_str}",
                    "disabled": False,
                    "time_format": convert_go_date_format(raw_t),
                }
            elif mod_name == "cmd_duration":
                thresh = curr.get("options", {}).get("threshold", 0)
                lead_str = format_dia_lead(curr, lead_chevron)
                trail_str = format_dia_trail(curr, connects=connects_to_next)
                icon_str = f"{icon}" if icon else ""
                self.modules["cmd_duration"] = {
                    "format": f"{lead_str}[ {icon_str}$duration ](fg:{fg} bg:{bg}){trail_str}",
                    "min_time": thresh,
                    "show_milliseconds": True,
                }
            else:
                raw_t = curr.get("raw_tmpl", "")
                lead_str = format_dia_lead(curr, lead_chevron)
                trail_str = format_dia_trail(curr, connects=connects_to_next)
                self.modules[mod_name] = {
                    "format": f"{lead_str}[ {icon}{raw_t} ](fg:{fg} bg:{bg}){trail_str}"
                }
            return

    def build_right_module(self, curr: Dict[str, Any], style: str, ribbon_bg: Optional[str]) -> None:
        mod_name = curr["mod_name"]
        icon = curr["icon"]
        raw_tmpl = curr["raw_tmpl"]
        fg = curr["fg"]
        bg = curr["bg"]
        lead = curr.get("leading", "")
        trail = curr.get("trailing", "")

        # Check for custom diamonds or diamond style (e.g. \ue0c5, \ue0ba, \ue0bc, \ue0b8, \ue0be)
        has_custom_diamond = any(c in (lead + trail) for c in ("\ue0c5", "\ue0ba", "\ue0bc", "\ue0b8", "\ue0be"))

        if has_custom_diamond:
            lead_str = f"[{lead}](fg:{bg})" if lead else ""
            trail_str = f"[{trail}](fg:{bg}) " if trail else ""
            if mod_name == "username":
                if curr.get("has_host"):
                    self.modules["username"] = {
                        "style_user": f"fg:{fg} bg:{bg}",
                        "style_root": f"fg:#FFEB3B bg:{bg}",
                        "format": f"{lead_str}[ $user ]($style)",
                        "show_always": True,
                    }
                    self.modules["hostname"] = {
                        "style": f"fg:{fg} bg:{bg}",
                        "format": f"[/ $hostname ]($style){trail_str}",
                        "ssh_only": False,
                    }
                else:
                    self.modules["username"] = {
                        "style_user": f"fg:{fg} bg:{bg}",
                        "style_root": f"fg:#FFEB3B bg:{bg}",
                        "format": f"{lead_str}[ $user ]($style){trail_str}",
                        "show_always": True,
                    }
            elif mod_name == "time":
                raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                icon_str = f"{icon}" if icon else ""
                if not trail and "\ue0ba" in lead:
                    trail_str = f"[](fg:{bg}) "
                self.modules["time"] = {
                    "format": f"{lead_str}[ {icon_str}$time ](fg:{fg} bg:{bg}){trail_str}",
                    "disabled": False,
                    "time_format": convert_go_date_format(raw_t),
                }
            elif mod_name == "cmd_duration":
                self.modules["cmd_duration"] = {
                    "format": f"{lead_str}[ {icon}$duration ](fg:{fg} bg:{bg}){trail_str}",
                    "min_time": 2000,
                }
            elif mod_name == "memory_usage":
                prefix = curr.get("prefix", "")
                self.modules["memory_usage"] = {
                    "disabled": False,
                    "threshold": -1,
                    "symbol": "",
                    "style": f"fg:{fg} bg:{bg}",
                    "format": f"{lead_str}{prefix}[ {icon}{raw_tmpl} ]($style){trail_str}",
                }
            elif mod_name == "battery":
                self.modules["battery"] = {
                    "disabled": False,
                    "format": f"{lead_str}[ {icon}{raw_tmpl} ](fg:{fg} bg:{bg}){trail_str}",
                }
            else:
                self.modules[mod_name] = {
                    "format": f"{lead_str}[ {icon}{raw_tmpl} ](fg:{fg} bg:{bg}){trail_str}",
                }
            return

        # Case 1: Flat style (no backgrounds)
        if style == "flat":
            prefix = curr.get("prefix", "")
            icon_s = f"{icon} " if icon and not icon.endswith(" ") else icon
            fmt = f"{prefix}[ {icon_s}{raw_tmpl} ](bold {fg})"
            res: Dict[str, Any] = {"format": fmt}
            if mod_name == "cmd_duration":
                res["min_time"] = 2_000
            elif mod_name == "time":
                res["disabled"] = False
                raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                res["time_format"] = convert_go_date_format(raw_t)
            elif mod_name == "username":
                res["show_always"] = True
                if curr.get("has_host"):
                    self.modules["hostname"] = {
                        "style": f"bold {fg}",
                        "format": "[/ $hostname ]($style) ",
                        "ssh_only": False,
                    }
            elif mod_name == "memory_usage":
                res["disabled"] = False
                res["threshold"] = -1
                res["symbol"] = ""
                res["style"] = f"bold {fg}"
                trail_delim = ""
                if curr.get("trailing") and curr.get("trailing") != " ":
                    trail_delim = f"[{curr['trailing']} ](fg:#9E9E9E)"
                res["format"] = f"{prefix}[{icon_s}{raw_tmpl} ]($style){trail_delim}"
            elif mod_name == "battery":
                res["disabled"] = False
                res["format"] = f"[{icon_s}{raw_tmpl} ](bold {fg})"
            elif prefix:
                res["format"] = f"{prefix}[ {icon_s}{raw_tmpl} ](bold {fg})"
            self.modules[mod_name] = res

        # Case 2: Powerline style with Starship PR #6017 prev_bg
        elif style == "powerline":
            effective_bg = bg or ribbon_bg or "#0b2942"
            if mod_name == "username" and curr.get("has_host"):
                self.modules["username"] = {
                    "style_user": f"fg:{fg} bg:{effective_bg}",
                    "style_root": f"fg:#FFEB3B bg:{effective_bg}",
                    "format": f"[](fg:{effective_bg} bg:prev_bg)[ $user ]($style)",
                    "show_always": True,
                }
                self.modules["hostname"] = {
                    "style": f"fg:{fg} bg:{effective_bg}",
                    "format": "[/ $hostname ]($style) ",
                    "ssh_only": False,
                }
            if mod_name == "git_branch":
                trail_glyph = curr.get("trailing", "") or "\ue0b0"
                trail_str = f"[{trail_glyph}](fg:{effective_bg}) "
                lead_glyph = curr.get("leading", "") or "\ue0b2"
                lead_str = f"[{lead_glyph}](fg:{effective_bg})"
                b_sym = icon or "󰊢 "
                self.modules["git_branch"] = {
                    "style": f"fg:{fg} bg:{effective_bg}",
                    "symbol": b_sym,
                    "format": f"{lead_str}[ {b_sym}$branch]($style)",
                }
                self.modules["git_status"] = {
                    "style": f"fg:{fg} bg:{effective_bg}",
                    "format": f"([ $ahead_behind$all_status]($style)){trail_str}",
                    "ahead": "↑${count} ",
                    "behind": "↓${count} ",
                    "modified": " ~${count} ",
                    "staged": " +${count} ",
                    "stashed": " ${count} ",
                    "untracked": " ${count} ",
                }
                return

            # In powerline style, intermediate modules must not have trailing diamonds to prevent breaking the ribbon.
            trail_glyph = curr.get("trailing", "") if mod_name == "time" else ""
            trail_str = f"[{trail_glyph}](fg:{effective_bg})" if trail_glyph else ""
            fmt = f"[](fg:{effective_bg} bg:prev_bg)[ {icon}{raw_tmpl} ](fg:{fg} bg:{effective_bg}){trail_str}"
            res = {"format": fmt}
            if mod_name == "cmd_duration":
                res["min_time"] = 2_000
            elif mod_name == "time":
                res["disabled"] = False
                raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                res["time_format"] = convert_go_date_format(raw_t)
            elif mod_name == "username":
                res["show_always"] = True
            elif mod_name == "memory_usage":
                res["disabled"] = False
                res["threshold"] = -1
                res["symbol"] = ""
            elif mod_name == "battery":
                res["disabled"] = False
            self.modules[mod_name] = res

        # Case 3: Unified Surface Ribbon (Capsule Themes)
        elif style == "ribbon":
            effective_bg = ribbon_bg or "#0b2942"
            if mod_name == "username" and curr.get("has_host"):
                self.modules["username"] = {
                    "style_user": f"fg:{fg} bg:{effective_bg}",
                    "style_root": f"fg:#FFEB3B bg:{effective_bg}",
                    "format": "[ $user ]($style)",
                    "show_always": True,
                }
                self.modules["hostname"] = {
                    "style": f"fg:{fg} bg:{effective_bg}",
                    "format": "[/ $hostname ]($style) ",
                    "ssh_only": False,
                }
                return
            fmt = f"[ {icon}{raw_tmpl} ](fg:{fg} bg:{effective_bg})"
            res = {"format": fmt}
            if mod_name == "cmd_duration":
                res["min_time"] = 2_000
            elif mod_name == "time":
                res["disabled"] = False
                raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                res["time_format"] = convert_go_date_format(raw_t)
            elif mod_name == "username":
                res["show_always"] = True
            elif mod_name == "memory_usage":
                res["disabled"] = False
                res["threshold"] = -1
                res["symbol"] = ""
            elif mod_name == "battery":
                res["disabled"] = False
            self.modules[mod_name] = res

        # Case 4: Floating Pills
        elif style == "pills":
            pill_bg = bg or "#303030"
            if mod_name == "username" and curr.get("has_host"):
                self.modules["username"] = {
                    "style_user": f"fg:{fg} bg:{pill_bg}",
                    "style_root": f"fg:#FFEB3B bg:{pill_bg}",
                    "format": f"[](fg:{pill_bg})[ $user ]($style)",
                    "show_always": True,
                }
                self.modules["hostname"] = {
                    "style": f"fg:{fg} bg:{pill_bg}",
                    "format": f"[/ $hostname ]($style)[](fg:{pill_bg}) ",
                    "ssh_only": False,
                }
                return
            fmt = f"[](fg:{pill_bg})[ {icon}{raw_tmpl} ](fg:{fg} bg:{pill_bg})[](fg:{pill_bg}) "
            res = {"format": fmt}
            if mod_name == "cmd_duration":
                res["min_time"] = 2_000
            elif mod_name == "time":
                res["disabled"] = False
                raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                res["time_format"] = convert_go_date_format(raw_t)
            elif mod_name == "username":
                res["show_always"] = True
            elif mod_name == "memory_usage":
                res["disabled"] = False
                res["threshold"] = -1
                res["symbol"] = ""
            elif mod_name == "battery":
                res["disabled"] = False
            self.modules[mod_name] = res

    def render_toml(
        self,
        line1_left_mods: List[str],
        line1_right_mods: List[str],
        subsequent_lines: List[List[str]],
        is_single_line: bool,
        right_style: str,
        ribbon_bg: Optional[str],
        has_rprompt: bool = False,
    ) -> str:
        lines = [
            "# =====================================================================",
            f"# Nirmana-Shell - Transpiled Theme: {self.theme_name}",
            "# Ported from Oh My Posh JSON schema via Nirmana OMP Transpiler v3.1",
            "# =====================================================================",
            "",
            "scan_timeout = 30",
            "command_timeout = 1000",
            f"add_newline = {'false' if is_single_line else 'true'}",
            "",
        ]

        lines.append("format = \"\"\"")

        pwr_sym = getattr(self, "powerline_symbol", "\ue0b0")
        if pwr_sym == "\ue0c4" and "sudo" in self.modules:
            badge_fmt = self.modules["sudo"].get("format", "").strip()
            if badge_fmt.startswith("[") or badge_fmt.startswith("[\ue0c7"):
                del self.modules["sudo"]
                if "$sudo" in line1_left_mods:
                    line1_left_mods.remove("$sudo")
                lines.append(f"{badge_fmt} \\")

        if getattr(self, "has_bracket_frame", False):
            bracket_fg = getattr(self, "bracket_fg", "#CB4B16")
            lines.append(f"[┏](fg:{bracket_fg})\\")
            if "sudo" in self.modules:
                del self.modules["sudo"]
            for idx, m in enumerate(line1_left_mods):
                if m == "$sudo":
                    line1_left_mods[idx] = rf"[\\[](fg:{bracket_fg})[⚡](fg:#ffffff)[\\]](fg:{bracket_fg})"

        # Line 1 Left
        for m in line1_left_mods:
            lines.append(f"{m}\\")

        # Line 1 Right (Separated by $fill if multi-line)
        if is_single_line:
            if not has_rprompt and right_style != "powerline":
                for m in line1_right_mods:
                    lines.append(f"{m}\\")
        elif self.use_fill and line1_right_mods:
            lines.append("$fill\\")
            if right_style == "ribbon":
                effective_bg = ribbon_bg or "#0b2942"
                lines.append("(\\")
                lines.append(f"[](fg:{effective_bg})\\")
                for m in line1_right_mods:
                    lines.append(f"{m}\\")
                lines.append(")\\")
            else:
                for m in line1_right_mods:
                    lines.append(f"{m}\\")

        # Line 2 and beyond
        for sub_mods in subsequent_lines:
            lines.append("$line_break\\")
            for m in sub_mods:
                lines.append(f"{m}\\")

        lines.append("\"\"\"")
        lines.append("")

        if not is_single_line and self.use_fill and line1_right_mods:
            lines.append("[fill]")
            lines.append('symbol = " "')
            lines.append("")

        for mod_name, mod_data in self.modules.items():
            lines.append(f"[{mod_name}]")
            for k, v in mod_data.items():
                if isinstance(v, bool):
                    lines.append(f"{k} = {str(v).lower()}")
                elif isinstance(v, (int, float)):
                    lines.append(f"{k} = {v}")
                elif isinstance(v, str):
                    escaped = v.replace("\\", "\\\\").replace('"', '\\"')
                    lines.append(f'{k} = "{escaped}"')
            lines.append("")

            if mod_name == "battery":
                lines.append("[[battery.display]]")
                lines.append("threshold = 100")
                bat_style = mod_data.get("style") or f"bold {mod_data.get('fg', '#A6E3A1')}"
                lines.append(f'style = "{bat_style}"')
                lines.append("")

        return "\n".join(lines)


def get_preview_generator():
    """Dynamically import generate-previews.py module if dependencies are present."""
    gen_script = Path(__file__).parent / "generate-previews.py"
    if gen_script.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("generate_previews", str(gen_script))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        except Exception:
            return None
    return None


def generate_theme_preview(toml_path: Path, theme_name: str, repo_root: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """Generate both ANSI text preview card (.previews/) and high-res PNG card (assets/previews/)."""
    import shutil
    import subprocess
    import tempfile

    preview_dir = repo_root / ".previews"
    output_dir = repo_root / "assets" / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    mock_base = Path(tempfile.mkdtemp(prefix="nirmana-prev-"))
    mock_dir = mock_base / "nirmana-shell"
    mock_dir.mkdir(parents=True, exist_ok=True)
    txt_path = preview_dir / f"{theme_name}.txt"
    png_path = None

    try:
        (mock_dir / "package.json").write_text('{"name": "nirmana-shell", "version": "1.0.0"}', encoding="utf-8")
        (mock_dir / "main.c").write_text("int main() {}", encoding="utf-8")
        (mock_dir / "app.py").write_text("print('hello')", encoding="utf-8")
        (mock_dir / "main.tf").write_text("terraform {}", encoding="utf-8")
        (mock_dir / ".terraform").mkdir(parents=True, exist_ok=True)
        (mock_dir / ".terraform" / "environment").write_text("example_corp-prod", encoding="utf-8")

        azure_dir = mock_base / ".azure"
        azure_dir.mkdir(parents=True, exist_ok=True)
        azure_profile = {
            "installationId": "nirmana-mock",
            "subscriptions": [
                {
                    "id": "mock-sub",
                    "name": "Contoso Production",
                    "user": {"name": "alice"},
                    "isDefault": True,
                }
            ],
        }
        (azure_dir / "azureProfile.json").write_text(json.dumps(azure_profile), encoding="utf-8")

        subprocess.run(["git", "-C", str(mock_dir), "init", "-b", "main", "--quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(mock_dir), "config", "user.name", "Nirmana"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(mock_dir), "config", "user.email", "nirmana@shell.local"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(mock_dir), "add", "-A"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(mock_dir), "commit", "-m", "init", "--quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(mock_dir / "main.c", "a", encoding="utf-8") as f:
            f.write("\n// change")

        env = os.environ.copy()
        env["STARSHIP_CONFIG"] = str(toml_path.resolve())
        env["AZURE_CONFIG_DIR"] = str(azure_dir)
        proc = subprocess.run(
            ["starship", "prompt", "--path", str(mock_dir), "--status", "0", "--cmd-duration", "2500", "--terminal-width", "88"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        raw_lines = proc.stdout.splitlines() if proc.returncode == 0 else []
        while raw_lines and not raw_lines[0].strip():
            raw_lines.pop(0)

        indented = "\n".join(f"  {line}" for line in raw_lines)
        esc = chr(27)
        card_content = f"""
  {esc}[1;35mCategory:{esc}[0m   {esc}[1;37m[Oh-My-Posh]{esc}[0m
  {esc}[1;36mTheme:{esc}[0m      {esc}[1;37m{theme_name}{esc}[0m
  {esc}[1;36mDetails:{esc}[0m    {esc}[0;37mCommunity theme ported from Oh My Posh{esc}[0m
  {esc}[0;90m──────────────────────────────────────────────────────────────────────────────{esc}[0m
  {esc}[1;33mRendered Prompt:{esc}[0m

{indented}{esc}[1;32mgit status{esc}[0m

  {esc}[0;90m──────────────────────────────────────────────────────────────────────────────{esc}[0m
  {esc}[0;90mControls: [Enter] Apply theme  |  [Esc] Cancel  |  [Arrows] Navigate{esc}[0m
"""
        txt_path.write_text(card_content, encoding="utf-8")
        print(f"  [PREVIEW] ANSI card -> {txt_path}")

        mod = get_preview_generator()
        if mod and hasattr(mod, "generate_preview_png") and hasattr(mod, "find_nerd_fonts"):
            nerd_fonts = mod.find_nerd_fonts()
            png_path = mod.generate_preview_png(txt_path, output_dir, nerd_fonts)
            print(f"  [PREVIEW] PNG card  -> {png_path}")
        else:
            print(f"  [PREVIEW] Tip: Run preview generation with:")
            print(f"            uv run --with rich --with resvg-py python scripts/generate-previews.py -t {theme_name}")

    except Exception as e:
        print(f"  [WARNING] Preview generation error: {e}", file=sys.stderr)
    finally:
        shutil.rmtree(mock_base, ignore_errors=True)

    return txt_path, png_path


def main():
    parser = argparse.ArgumentParser(
        description="Transpile Oh My Posh theme JSON to clean Starship TOML for Nirmana-Shell."
    )
    parser.add_argument("input", help="Path to .omp.json file, HTTP/HTTPS URL, or OMP theme name")
    parser.add_argument("-o", "--output", help="Output path for .toml file or directory (if batch)")
    parser.add_argument("-n", "--name", help="Theme name identifier override")
    parser.add_argument("--style", choices=["capsule", "powerline", "flat"], help="Visual style override")
    parser.add_argument("--pills", action="store_true", help="Use floating pills for right side instead of unified ribbon")
    parser.add_argument("--ribbon-bg", help="Override ribbon surface background color (e.g. '#0b2942')")
    parser.add_argument("--no-fill", action="store_true", help="Disable Nirmana right-aligned $fill layout")
    parser.add_argument("--no-runtimes", action="store_true", help="Do not inject developer runtime modules")
    parser.add_argument("--add-runtimes", action="store_true", help="Force injection of developer runtime modules even on flat themes")
    parser.add_argument("--no-preview", action="store_true", help="Skip generating ANSI and PNG preview cards")
    parser.add_argument("--batch", action="store_true", help="Treat input as a directory of .omp.json files")

    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent

    if args.batch:
        input_dir = Path(args.input)
        if not input_dir.is_dir():
            print(f"Error: {input_dir} is not a directory.", file=sys.stderr)
            sys.exit(1)
        out_dir = Path(args.output) if args.output else repo_root / "themes"
        out_dir.mkdir(parents=True, exist_ok=True)

        json_files = sorted(input_dir.glob("*.omp.json"))
        print(f"Found {len(json_files)} OMP themes in {input_dir}. Transpiling...")
        for jf in json_files:
            try:
                data, theme_name = parse_omp_json(str(jf))
                transpiler = OmpTranspiler(
                    data,
                    theme_name=theme_name,
                    use_fill=not args.no_fill,
                    left_style_override=args.style,
                    use_pills=args.pills,
                    ribbon_bg_override=args.ribbon_bg,
                    add_runtimes=not args.no_runtimes,
                    force_runtimes=args.add_runtimes,
                )
                toml_content = transpiler.transpile()
                out_file = out_dir / f"{theme_name}.toml"
                out_file.write_text(toml_content, encoding="utf-8")
                print(f"  [OK] {theme_name} -> {out_file}")

                if not args.no_preview:
                    generate_theme_preview(out_file, theme_name, repo_root)
            except Exception as e:
                print(f"  [ERROR] {jf.name}: {e}", file=sys.stderr)
        print("Batch transpilation complete.")
        return

    data, parsed_name = parse_omp_json(args.input)
    theme_name = args.name or parsed_name
    theme_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "-", theme_name).strip("-")

    transpiler = OmpTranspiler(
        data,
        theme_name=theme_name,
        use_fill=not args.no_fill,
        left_style_override=args.style,
        use_pills=args.pills,
        ribbon_bg_override=args.ribbon_bg,
        add_runtimes=not args.no_runtimes,
        force_runtimes=args.add_runtimes,
    )
    toml_content = transpiler.transpile()

    if args.output:
        out_path = Path(args.output)
        if out_path.is_dir():
            out_path = out_path / f"{theme_name}.toml"
    else:
        out_path = repo_root / "themes" / f"{theme_name}.toml"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(toml_content, encoding="utf-8")
    print(f"Successfully transpiled Oh My Posh theme '{theme_name}' -> '{out_path}'")

    if not args.no_preview:
        generate_theme_preview(out_path, theme_name, repo_root)


if __name__ == "__main__":
    main()
