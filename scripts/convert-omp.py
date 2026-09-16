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
        powerline_count = sum(
            1 for s in all_segs
            if any(g in (s.get("leading_diamond", "") + s.get("trailing_diamond", "") + s.get("powerline_symbol", "") + s.get("template", "")) for g in ("\ue0b0", "\ue0b2", "\ue0b1", "\ue0b3"))
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

        if not has_any_bg:
            theme_style = "flat"
        elif has_pill_diamonds:
            theme_style = "capsule"
        elif powerline_count >= capsule_count and powerline_count > 0:
            theme_style = "powerline"
        elif capsule_count > 0:
            theme_style = "capsule"
        else:
            theme_style = "capsule" if has_any_bg else "flat"

        if self.left_style_override:
            theme_style = self.left_style_override

        # Step 2: Group blocks into physical lines
        prompt_lines: List[Dict[str, List[Dict[str, Any]]]] = []
        curr_line: Dict[str, List[Dict[str, Any]]] = {"left": [], "right": []}

        for idx, b in enumerate(blocks):
            if idx > 0 and b.get("newline"):
                prompt_lines.append(curr_line)
                curr_line = {"left": [], "right": []}

            align = b.get("alignment", "left")
            if b.get("type") == "rprompt":
                align = "right"

            curr_line[align].extend(b.get("segments", []))

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

        # Step 3: Extract prompt character from the last line (status or text segment)
        line_character = None
        has_pill_prompt_user = False
        last_left = prompt_lines[-1]["left"] if prompt_lines else []
        connector_span = ""
        for s in list(last_left):
            stype = s.get("type")
            tmpl = s.get("template", "")
            fg, bg = self.get_seg_colors(s)
            if stype in ("text", "status") and any(c in tmpl for c in ("\u2570", "╰")):
                col = fg or bg or "#FEF5ED"
                connector_span = f"[{tmpl.strip()}](fg:{col})"
                last_left.remove(s)
                break

        for s in reversed(last_left):
            stype = s.get("type")
            tmpl = s.get("template", "")
            fg, bg = self.get_seg_colors(s)
            lead = s.get("leading_diamond", "")
            trail = s.get("trailing_diamond", "")
            has_prompt_char = any(c in tmpl for c in ("\u276f", "\u276e", "❯", "❮", ">", "$", "#", "➜", "λ", "", "", "▶", "»"))
            if stype in ("text", "status") or (stype == "session" and has_prompt_char):
                clean_sym = re.sub(r"\{\{.*?\}\}", "", tmpl)
                clean_sym = re.sub(r"<[^>]+>", "", clean_sym).strip()
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

        # Relocate metrics and runtimes from left to right on Line 1 ONLY if right side is initially empty
        if not line1_right and not (is_single_line and theme_style == "powerline"):
            relocated = []
            remaining_l1 = []
            for s in line1_left:
                stype = s.get("type", "")
                if stype in ("executiontime", "sysinfo", "memory", "battery", "time") or stype in RUNTIME_MAPPINGS:
                    relocated.append(s)
                    continue
                remaining_l1.append(s)
            prompt_lines[0]["left"] = remaining_l1
            if relocated:
                line1_right[:0] = relocated

        # Check if runtimes should be injected
        has_orig_runtimes = any(s.get("type") in RUNTIME_MAPPINGS for s in all_segs)
        should_inject_runtimes = self.force_runtimes or (
            self.add_runtimes and has_orig_runtimes
        )

        # Parse Line 1 Left segments
        parsed_l1_left = []
        for s in prompt_lines[0]["left"]:
            mod = self.parse_segment(s)
            if mod:
                parsed_l1_left.append(mod)

        # Check if directory or git are missing completely across all lines
        all_parsed_segs = [self.parse_segment(s) for pl in prompt_lines for s in pl["left"] + pl["right"]]
        all_parsed_names = {p["mod_name"] for p in all_parsed_segs if p}

        if "directory" not in all_parsed_names:
            parsed_l1_left.insert(0, {
                "mod_name": "directory", "var_name": "$directory",
                "fg": "#82AAFF" if theme_style == "flat" else "#011627",
                "bg": None if theme_style == "flat" else "#82AAFF",
                "leading": "" if theme_style == "flat" else "╭─",
                "trailing": "" if theme_style == "flat" else "",
                "icon": " ", "raw_tmpl": "$path",
                "options": {},
            })

        if "git_branch" not in all_parsed_names:
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
        for m in parsed_l1_left:
            self.build_left_module(m, theme_style)
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

        # Inject developer runtimes if appropriate
        if should_inject_runtimes and not (is_single_line and theme_style == "powerline"):
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
            for s in pl["left"]:
                mod = self.parse_segment(s)
                if mod:
                    if mod.get("mod_name") != "connector":
                        self.build_left_module(mod, theme_style)
                    if mod["var_name"] not in curr_sub_mods:
                        curr_sub_mods.append(mod["var_name"])
                        if mod["mod_name"] == "git_branch" and "$git_status" not in curr_sub_mods:
                            curr_sub_mods.append("$git_status")
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
            if not subsequent_line_mods:
                subsequent_line_mods.append([])
            if has_pill_prompt_user and "$username" not in subsequent_line_mods[-1]:
                subsequent_line_mods[-1].append("$username")
            subsequent_line_mods[-1].append("$character")

        # Configure character module for single-line powerline
        if is_single_line and theme_style == "powerline":
            dir_mod = next((p for p in parsed_l1_left if p["mod_name"] == "directory"), None)
            git_mod = next((p for p in parsed_l1_left if p["mod_name"] == "git_branch"), None)
            is_same_bg_powerline = bool(dir_mod and git_mod and dir_mod.get("bg") == git_mod.get("bg"))
            if is_same_bg_powerline:
                self.modules["character"] = {
                    "format": "$symbol",
                    "success_symbol": "",
                    "error_symbol": "",
                }
            else:
                self.modules["character"] = {
                    "format": "[](fg:prev_bg) ",
                    "success_symbol": "",
                    "error_symbol": "",
                }

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
        stype = s.get("type", "")
        fg, bg = self.get_seg_colors(s)
        tmpl = s.get("template", "")
        options = s.get("options") or s.get("properties") or {}
        lead = s.get("leading_diamond", "")
        trail = s.get("trailing_diamond", "") or s.get("powerline_symbol", "")

        extra_text = ""
        if stype == "session":
            m = re.search(r"\{\{\s*\.UserName\s*\}\}\s*(.*)", tmpl)
            if m:
                extra_text = m.group(1)
        elif stype == "executiontime":
            if "\ue601" in tmpl:
                options["icon"] = " "
            elif "\ueba2" in tmpl:
                options["icon"] = " "

        if stype == "os":
            win_sym = options.get("windows") or ""
            return {
                "mod_name": "os", "var_name": "$os",
                "fg": fg or "#011627", "bg": bg or "#21c7a8",
                "leading": lead, "trailing": trail,
                "icon": win_sym, "raw_tmpl": "$symbol",
                "options": options,
                "template": tmpl,
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
            }
        elif stype == "path":
            has_icon = any(x in tmpl for x in ("\uf07c", "\ue5ff", "\uf115", ".Icon"))
            icon = ""
            if has_icon:
                icon = " " if "\ue5ff" in tmpl else " "
            return {
                "mod_name": "directory", "var_name": "$directory",
                "fg": fg or ("#FEF5ED" if self.has_top_connector else "#82AAFF"), "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": icon, "raw_tmpl": "$path",
                "options": options,
                "template": tmpl,
            }
        elif stype == "git":
            raw_b = options.get("branch_icon", "")
            b_icon = " "
            if "\ue725" in raw_b or "\ue725" in tmpl:
                b_icon = " "
            elif "\ue0a0" in raw_b or "\ue0a0" in tmpl:
                b_icon = " "
            return {
                "mod_name": "git_branch", "var_name": "$git_branch",
                "fg": fg or "#addb67", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": b_icon, "raw_tmpl": "$branch",
                "options": options,
                "template": tmpl,
            }
        elif stype == "session":
            has_host = "{{ .HostName }}" in tmpl or ".HostName" in tmpl
            has_icon = any(x in tmpl for x in ("\uf007", "\uf2bd", "\ue712", ".Icon"))
            icon = " " if has_icon else ""
            return {
                "mod_name": "username", "var_name": "$username",
                "fg": fg or "#43CCEA", "bg": bg,
                "leading": lead, "trailing": trail,
                "extra_text": extra_text,
                "has_host": has_host,
                "icon": icon, "raw_tmpl": "$user",
                "options": options,
                "template": tmpl,
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
            }
        elif stype == "shell":
            return {
                "mod_name": "shell", "var_name": "$shell",
                "fg": fg or "#011627", "bg": bg or "#FEF5ED",
                "leading": lead, "trailing": trail,
                "icon": " ", "raw_tmpl": "$indicator",
                "options": options,
                "template": tmpl,
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
                }
            return None
        elif stype == "time":
            has_icon = any(x in tmpl for x in ("\uf017", "\ue383", ".Icon"))
            icon = " " if has_icon else ""
            if "\u2665" in tmpl or "♥" in tmpl:
                icon = "♡ "
            return {
                "mod_name": "time", "var_name": "$time",
                "fg": fg or ("#FEF5ED" if self.has_top_connector else "#82AAFF"), "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": icon, "raw_tmpl": "$time",
                "options": options,
                "template": tmpl,
            }
        elif stype in ("battery",):
            return {
                "mod_name": "battery", "var_name": "$battery",
                "fg": fg or "#A6E3A1", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": "󰁹 ", "raw_tmpl": "$percentage",
                "options": options,
                "template": tmpl,
            }
        elif stype in ("sysinfo", "memory"):
            return {
                "mod_name": "memory_usage", "var_name": "$memory_usage",
                "fg": fg or "#C792EA", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": "󰍛 ", "raw_tmpl": "$ram_pct",
                "options": options,
                "template": tmpl,
            }
        elif stype in RUNTIME_MAPPINGS:
            m_name, v_name, ic, def_fg = RUNTIME_MAPPINGS[stype]
            return {
                "mod_name": m_name, "var_name": v_name,
                "fg": fg or def_fg, "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": ic, "raw_tmpl": "$version",
                "options": options,
                "template": tmpl,
            }

        return None

    def build_left_module(self, curr: Dict[str, Any], style: str) -> None:
        mod_name = curr["mod_name"]
        bg = curr["bg"]
        fg = curr["fg"] or "#ffffff"
        icon = curr["icon"]

        # Case 1: Flat style or segment without background
        if style == "flat" or not bg:
            lead_span = parse_omp_markup(curr.get("leading"), fg)
            trail_span = parse_omp_markup(curr.get("trailing"), fg)
            extra_span = parse_omp_markup(curr.get("extra_text"), fg)

            if mod_name == "directory":
                fg_col = fg or "#FEF5ED"
                self.modules["directory"] = {
                    "format": f"{lead_span}[{icon}$path ](fg:{fg_col}){trail_span} ",
                    "truncation_length": 3,
                    "truncation_symbol": "…/",
                }
            elif mod_name == "git_branch":
                self.modules["git_branch"] = {
                    "format": f"[{icon}$branch](bold {fg})",
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
                if curr.get("has_host"):
                    self.modules["username"] = {
                        "format": f"{lead_span}[$user](bold {fg})",
                        "show_always": False,
                    }
                    self.modules["hostname"] = {
                        "format": f"[@$hostname ](bold {fg}) ",
                        "ssh_only": True,
                    }
                else:
                    self.modules["username"] = {
                        "format": f"{lead_span}[$user ](bold {fg}){extra_span} ",
                        "show_always": False,
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
                self.modules["memory_usage"] = {
                    "format": f"[ MEM: $ram_pct ](bold {fg}) ",
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
            else:
                icon_str = f" {icon}" if icon else " "
                raw_t = curr.get("raw_tmpl", "")
                self.modules[mod_name] = {
                    "format": f"[](fg:{bg})[{icon_str}{raw_t} ](fg:{fg} bg:{bg})[](fg:{bg}) ",
                }
            return

        # Case 3: Powerline chevron style
        if style == "powerline":
            l1_mods = getattr(self, "parsed_l1_left", [])
            is_first = bool(l1_mods and curr == l1_mods[0])
            lead_chevron = "" if is_first else f"[](fg:prev_bg bg:{bg})"

            if mod_name == "os":
                lead_str = f"[{curr['leading']}](fg:{bg})" if curr.get("leading") else ""
                trail_str = ""
                if curr.get("trailing"):
                    if "<transparent" in curr["trailing"]:
                        trail_str = f"[](fg:#292929 bg:{bg})"
                    else:
                        trail_str = f"[{curr['trailing']}](fg:{bg}) "
                self.modules["os"] = {
                    "disabled": False,
                    "style": f"fg:{fg} bg:{bg}",
                    "format": f"{lead_str}[ $symbol ]($style){trail_str}",
                }
                self.modules["os.symbols"] = {
                    "Windows": "󰕮",
                    "Ubuntu": "",
                    "Macos": "",
                    "Linux": "",
                }
            elif mod_name == "shell":
                idx = l1_mods.index(curr) if curr in l1_mods else -1
                prev_mod = l1_mods[idx - 1] if idx > 0 else None
                same_bg_as_prev = bool(prev_mod and prev_mod.get("bg") == bg)
                lead_str = "" if same_bg_as_prev else (f"[{curr['leading']}](fg:{bg})" if curr.get("leading") else "")
                trail_str = ""
                if curr.get("trailing"):
                    if "<transparent" in curr["trailing"]:
                        trail_str = f"[](fg:#292929 bg:{bg}) "
                    else:
                        trail_str = f"[{curr['trailing']}](fg:{bg}) "
                self.modules["shell"] = {
                    "disabled": False,
                    "powershell_indicator": "pwsh",
                    "bash_indicator": "bash",
                    "zsh_indicator": "zsh",
                    "style": f"fg:{fg} bg:{bg}",
                    "format": f"{lead_str}[  $indicator ]($style){trail_str}",
                }
            elif mod_name == "memory_usage":
                lead_str = f"[{curr['leading']}](fg:{bg})" if curr.get("leading") else ""
                trail_str = ""
                if curr.get("trailing"):
                    if "<transparent" in curr["trailing"]:
                        trail_str = f"[](fg:#292929 bg:{bg}) "
                    else:
                        trail_str = f"[{curr['trailing']}](fg:{bg}) "
                self.modules["memory_usage"] = {
                    "disabled": False,
                    "threshold": -1,
                    "style": f"fg:{fg} bg:{bg}",
                    "symbol": "󰍛",
                    "format": f"{lead_str}[ $symbol MEM: $ram_pct | $ram $symbol ]($style){trail_str}",
                }
            elif mod_name == "sudo":
                if bg:
                    user_mod = next((p for p in l1_mods if p["mod_name"] == "username"), None)
                    next_bg = user_mod["bg"] if user_mod and user_mod.get("bg") else "#ffffff"
                    self.modules["sudo"] = {
                        "style": f"fg:{fg} bg:{bg}",
                        "format": f"[ {icon}]($style)[](fg:{bg} bg:{next_bg})",
                        "disabled": False,
                    }
                else:
                    self.modules["sudo"] = {
                        "format": f"[# ](fg:{fg}) " if "#" in curr.get("template", "") else f"[ {icon}](fg:{fg}) ",
                        "disabled": False,
                    }
            elif mod_name == "username":
                if bg:
                    has_lead = bool("os" in self.modules or (l1_mods and l1_mods[0]["mod_name"] not in ("username", "sudo")))
                    lead = f"[](fg:prev_bg bg:{bg})" if has_lead else ""
                    self.modules["username"] = {
                        "format": f"{lead}[ {icon}$user ](fg:{fg} bg:{bg})",
                        "show_always": True,
                    }
                else:
                    self.modules["username"] = {
                        "format": f"[$user ](fg:{fg})",
                        "show_always": False,
                    }
            elif mod_name == "directory":
                icon_part = f"{icon}" if icon else ""
                tmpl = curr.get("template", "")
                if "<transparent>" in tmpl:
                    self.modules["directory"] = {
                        "format": f"[](fg:#292929 bg:{bg})[ {icon_part}$path ](fg:{fg} bg:{bg})",
                        "truncation_length": 3,
                        "truncation_symbol": "…/",
                    }
                else:
                    self.modules["directory"] = {
                        "format": f"{lead_chevron}[ {icon_part}$path ](fg:{fg} bg:{bg})",
                        "truncation_length": 3,
                        "truncation_symbol": "…/",
                    }
            elif mod_name == "git_branch":
                icon_part = f"{icon}" if icon else ""
                dir_mod = next((p for p in l1_mods if p["mod_name"] == "directory"), None)
                same_bg = bool(dir_mod and dir_mod.get("bg") == bg)
                if same_bg:
                    self.modules["git_branch"] = {
                        "format": f"[ {icon_part}$branch ](fg:{fg} bg:{bg})"
                    }
                    self.modules["git_status"] = {
                        "format": f"([$all_status$ahead_behind ](fg:{fg} bg:{bg}))[](fg:{bg}) ",
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
                        "format": f"[](fg:prev_bg bg:{bg})[ {icon_part}$branch ](fg:{fg} bg:{bg})"
                    }
                    self.modules["git_status"] = {
                        "format": f"([$all_status$ahead_behind ](fg:{fg} bg:{bg}))",
                        "modified": " ✎",
                        "staged": " ",
                        "stashed": " ",
                        "ahead": " ⇡${count}",
                        "behind": " ⇣${count}",
                        "diverged": " ⇕⇡${ahead_count}⇣${behind_count}",
                    }
            elif mod_name == "status":
                if bg:
                    self.modules["status"] = {
                        "format": f"[](fg:prev_bg bg:{bg})[ $status ](fg:{fg} bg:{bg})",
                        "disabled": False,
                    }
                else:
                    sym = curr.get("icon") or "❌"
                    self.modules["status"] = {
                        "format": f"[$symbol ](fg:{fg})",
                        "symbol": sym,
                        "disabled": False,
                    }
            elif mod_name in RUNTIME_MAPPINGS or mod_name in [r[0] for r in STANDARD_DEVELOPER_RUNTIMES] or mod_name == "python":
                self.modules[mod_name] = {
                    "format": f"[](fg:prev_bg bg:{bg})[ {icon}$version ](fg:{fg} bg:{bg})"
                }
            elif mod_name == "time":
                raw_t = curr.get("options", {}).get("time_format", "15:04:05")
                self.modules["time"] = {
                    "format": f"{lead_chevron}[ {icon}$time ](fg:{fg} bg:{bg})",
                    "disabled": False,
                    "time_format": convert_go_date_format(raw_t),
                }
            elif mod_name == "cmd_duration":
                thresh = curr.get("options", {}).get("threshold", 0)
                lead_str = f"[{curr['leading']}](fg:{bg})" if curr.get("leading") else lead_chevron
                trail_str = f"[{curr['trailing']}](fg:{bg}) " if curr.get("trailing") else ""
                icon_str = f"{icon}" if icon else ""
                self.modules["cmd_duration"] = {
                    "format": f"{lead_str}[ {icon_str}$duration ](fg:{fg} bg:{bg}){trail_str}",
                    "min_time": thresh,
                    "show_milliseconds": True,
                }
            else:
                raw_t = curr.get("raw_tmpl", "")
                self.modules[mod_name] = {
                    "format": f"{lead_chevron}[ {icon}{raw_t} ](fg:{fg} bg:{bg})"
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
            else:
                self.modules[mod_name] = {
                    "format": f"{lead_str}[ {icon}{raw_tmpl} ](fg:{fg} bg:{bg}){trail_str}",
                }
            return

        # Case 1: Flat style (no backgrounds)
        if style == "flat":
            fmt = f"[ {icon}{raw_tmpl} ](bold {fg})"
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

        subprocess.run(["git", "-C", str(mock_dir), "init", "-b", "main", "--quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(mock_dir), "config", "user.name", "Nirmana"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(mock_dir), "config", "user.email", "nirmana@shell.local"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(mock_dir), "add", "-A"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", str(mock_dir), "commit", "-m", "init", "--quiet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(mock_dir / "main.c", "a", encoding="utf-8") as f:
            f.write("\n// change")

        env = os.environ.copy()
        env["STARSHIP_CONFIG"] = str(toml_path.resolve())
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
