#!/usr/bin/env python3
"""
Nirmana-Shell - Oh My Posh to Starship Theme Transpiler (Overhauled)
Converts Oh My Posh theme JSON configurations (*.omp.json) into clean,
high-performance Starship themes (*.toml) with accurate powerline color chaining,
faithful single-line/multi-line layout detection, and authentic prompt glyphs.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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


def convert_go_date_format(go_fmt: str) -> str:
    """Convert Go time reference format to strftime format."""
    res = re.sub(r"<[^>]+>", "", go_fmt)
    for go_pat, strftime_pat in GO_DATE_TO_STRFTIME:
        res = re.sub(r"\b" + re.escape(go_pat) + r"\b", strftime_pat, res)
    return res


def clean_template_tags(template_str: str, current_bg: Optional[str] = None, palette: Optional[Dict[str, str]] = None) -> str:
    """Clean and translate OMP template tags into Starship format strings."""
    if not template_str:
        return ""

    palette = palette or {}

    def normalize_color(col: str) -> str:
        if not col or col.strip().lower() == "transparent":
            return ""
        if col.startswith("p:"):
            key = col[2:]
            col = palette.get(key, key)
        else:
            col = palette.get(col, col)

        if not col or str(col).strip().lower() == "transparent":
            return ""

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

    def resolve_tag_col(c: str) -> str:
        if c == "background" and current_bg:
            return current_bg
        return normalize_color(c)

    def repl_fg_bg(m):
        fg, bg = resolve_tag_col(m.group(1)), resolve_tag_col(m.group(2))
        txt = m.group(3)
        style = []
        if fg and fg != "transparent":
            style.append(f"fg:{fg}")
        if bg and bg != "transparent":
            style.append(f"bg:{bg}")
        return f"[{txt}]({' '.join(style)})" if style else txt

    def repl_color(m):
        col = resolve_tag_col(m.group(1))
        txt = m.group(2)
        if not col or col == "transparent":
            return txt
        return f"[{txt}]({col})"

    s = re.sub(r"<([^,>]+),([^>]+)>(.*?)</>", repl_fg_bg, template_str)
    s = re.sub(r"<#?([0-9a-fA-F]{3,6}|[a-zA-Z0-9_\-:]+)>(.*?)</>", repl_color, s)
    s = re.sub(r"<[^>]+>", "", s)
    return s


def parse_omp_json(source: str) -> Tuple[Dict[str, Any], str]:
    """Load JSON from local path, URL, or Oh My Posh theme name."""
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
            headers={"User-Agent": "Nirmana-Shell-Transpiler/2.0"},
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
    def __init__(self, data: Dict[str, Any], theme_name: str, use_fill: bool = True):
        self.data = data
        self.theme_name = theme_name
        self.use_fill = use_fill
        self.palette = data.get("palette", {})
        self.modules: Dict[str, Dict[str, Any]] = {}

    def resolve_color(self, col: Optional[str]) -> Optional[str]:
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

        # Step 1: Classify blocks into Left (Line 1), Right (Line 1), and Newline (Line 2+)
        left_blocks = []
        right_blocks = []
        newline_blocks = []

        for idx, b in enumerate(blocks):
            b_type = b.get("type", "prompt")
            alignment = b.get("alignment", "left")
            newline = b.get("newline", False)

            if idx > 0 and newline:
                newline_blocks.append(b)
            elif alignment == "right" or b_type == "rprompt":
                right_blocks.append(b)
            else:
                left_blocks.append(b)

        is_single_line = len(newline_blocks) == 0

        # Step 2: Extract segments
        left_segs = []
        for b in left_blocks:
            left_segs.extend(b.get("segments", []))

        right_segs = []
        for b in right_blocks:
            right_segs.extend(b.get("segments", []))

        # Step 3: Extract Line 2 character & sudo if multi-line
        line2_character = None
        line2_sudo = None
        for b in newline_blocks:
            for s in b.get("segments", []):
                stype = s.get("type")
                tmpl = s.get("template", "")
                fg, bg = self.get_seg_colors(s)

                if stype == "root":
                    sym = " " if "\uf0e7" in tmpl else "⚡ "
                    col = fg or bg or "yellow"
                    line2_sudo = {
                        "disabled": False,
                        "symbol": sym,
                        "format": f"[{sym}]({col}) ",
                    }
                elif stype in ("text", "status"):
                    # Extract glyph directly from template
                    clean_sym = re.sub(r"\{\{.*?\}\}", "", tmpl)
                    clean_sym = re.sub(r"<[^>]+>", "", clean_sym).strip()
                    if len(clean_sym) > 4:
                        # Skip long text/messages like "Error, check your command"
                        continue
                    # Escape literal $, [, ], (, ) for Starship parser
                    clean_sym = clean_sym.replace("\\", "")
                    clean_sym = clean_sym.replace("$", "\\$")
                    clean_sym = clean_sym.replace("[", "\\[").replace("]", "\\]")
                    clean_sym = clean_sym.replace("(", "\\(").replace(")", "\\)")
                    sym = f"{clean_sym} " if clean_sym else "❯ "

                    col = fg or bg or "green"
                    err_col = "#ef5350"
                    for t in s.get("foreground_templates", []):
                        m = re.search(r"#([0-9a-fA-F]{3,6})", t)
                        if m:
                            err_col = f"#{m.group(1)}"
                            break
                    line2_character = {
                        "success_symbol": f"[{sym}](bold {col}) ",
                        "error_symbol": f"[{sym}](bold {err_col}) ",
                    }

        # Step 4: Process Line 1 Left segments
        line1_left_mods = []
        parsed_left = []
        pending_lead = None  # leading_diamond from skipped segments (e.g. 'os')
        for s in left_segs:
            mod_info = self.parse_segment(s)
            if mod_info:
                # Propagate leading diamond from skipped segment
                if pending_lead and not mod_info.get("leading"):
                    mod_info["leading"] = pending_lead
                pending_lead = None
                parsed_left.append(mod_info)
            else:
                # Capture leading diamond from skipped segment for propagation
                raw_lead = s.get("leading_diamond", "")
                if raw_lead:
                    cleaned = re.sub(r"<[^>]+>", "", raw_lead).strip()
                    if cleaned:
                        pending_lead = cleaned

        # Ensure directory is present
        if not any(p["mod_name"] == "directory" for p in parsed_left):
            parsed_left.insert(0, {
                "mod_name": "directory",
                "var_name": "$directory",
                "fg": "cyan",
                "bg": None,
                "leading": "",
                "trailing": "",
                "icon": " ",
                "raw_tmpl": "$path",
                "options": {},
            })

        # Ensure git is present
        if not any(p["mod_name"] == "git_branch" for p in parsed_left):
            dir_idx = next((i for i, p in enumerate(parsed_left) if p["mod_name"] == "directory"), 0)
            parsed_left.insert(dir_idx + 1, {
                "mod_name": "git_branch",
                "var_name": "$git_branch",
                "fg": "purple",
                "bg": None,
                "leading": "",
                "trailing": "",
                "icon": " ",
                "raw_tmpl": "$branch",
                "options": {},
            })

        # Build module definitions for Line 1 Left with background-to-background transitions
        for i, curr in enumerate(parsed_left):
            prev = parsed_left[i - 1] if i > 0 else None
            next_seg = parsed_left[i + 1] if i + 1 < len(parsed_left) else None
            is_last = (i == len(parsed_left) - 1)

            mod_def = self.build_module_format(curr, prev, next_seg, is_last=is_last)
            self.modules[curr["mod_name"]] = mod_def

            if curr["var_name"] not in line1_left_mods:
                line1_left_mods.append(curr["var_name"])
                if curr["mod_name"] == "git_branch" and "$git_status" not in line1_left_mods:
                    line1_left_mods.append("$git_status")

        # Step 5: Process Line 1 Right segments
        line1_right_mods = []
        parsed_right = []
        pending_lead = None
        for s in right_segs:
            mod_info = self.parse_segment(s)
            if mod_info:
                if pending_lead and not mod_info.get("leading"):
                    mod_info["leading"] = pending_lead
                pending_lead = None
                parsed_right.append(mod_info)
            else:
                raw_lead = s.get("leading_diamond", "")
                if raw_lead:
                    cleaned = re.sub(r"<[^>]+>", "", raw_lead).strip()
                    if cleaned:
                        pending_lead = cleaned

        for i, curr in enumerate(parsed_right):
            prev = parsed_right[i - 1] if i > 0 else None
            next_seg = parsed_right[i + 1] if i + 1 < len(parsed_right) else None
            is_first = (i == 0)

            mod_def = self.build_right_module_format(curr, prev, next_seg, is_first=is_first)
            self.modules[curr["mod_name"]] = mod_def

            if curr["var_name"] not in line1_right_mods:
                line1_right_mods.append(curr["var_name"])

        # Configure Line 2 character / sudo
        line2_mods = []
        if not is_single_line:
            if line2_sudo:
                self.modules["sudo"] = line2_sudo
                line2_mods.append("$sudo")
            self.modules["character"] = line2_character or {
                "success_symbol": "[❯](bold green) ",
                "error_symbol": "[❯](bold red) ",
            }
            line2_mods.append("$character")
        else:
            # Single-line theme: input character immediately on Line 1
            self.modules["character"] = {
                "success_symbol": "",
                "error_symbol": "",
            }
            line1_left_mods.append("$character")

        return self.render_toml(line1_left_mods, line1_right_mods, line2_mods, is_single_line)

    def parse_segment(self, s: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        stype = s.get("type", "")
        fg, bg = self.get_seg_colors(s)
        tmpl = s.get("template", "")
        options = s.get("options") or s.get("properties") or {}
        lead = s.get("leading_diamond", "")
        trail = s.get("trailing_diamond", "") or s.get("powerline_symbol", "")

        if lead:
            lead = re.sub(r"<[^>]+>", "", lead).strip()
        if trail:
            trail = re.sub(r"<[^>]+>", "", trail).strip()

        runtime_map = {
            "node": ("nodejs", "$nodejs", "󰎙 ", fg or "#6CA35E"),
            "go": ("golang", "$golang", " ", fg or "#8ED1F7"),
            "python": ("python", "$python", "󰌠 ", fg or "#FFDE57"),
            "rust": ("rust", "$rust", " ", fg or "#DEA584"),
            "ruby": ("ruby", "$ruby", " ", fg or "#AE1401"),
            "java": ("java", "$java", " ", fg or "#ED8B00"),
            "dotnet": ("dotnet", "$dotnet", "󰪮 ", fg or "#512BD4"),
            "php": ("php", "$php", " ", fg or "#777BB4"),
            "bun": ("bun", "$bun", "󰎙 ", fg or "#FF9F43"),
            "dart": ("dart", "$dart", " ", fg or "#7FD5EA"),
            "julia": ("julia", "$julia", " ", fg or "#4063D8"),
            "shell": ("shell", "$shell", " ", fg or "#0077c2"),
            "package": ("package", "$package", "󰏗 ", fg or "#AEA4BF"),
        }

        if stype == "path":
            icon = " " if "\ue5ff" in tmpl else " "
            return {
                "mod_name": "directory", "var_name": "$directory",
                "fg": fg or "cyan", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": icon, "raw_tmpl": "$path",
                "options": options,
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
                "fg": fg or "white", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": b_icon, "raw_tmpl": "$branch",
                "options": options,
            }
        elif stype == "session":
            return {
                "mod_name": "username", "var_name": "$username",
                "fg": fg or "white", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": "", "raw_tmpl": "$user",
                "options": options,
            }
        elif stype == "executiontime":
            icon = " "
            if "\ueba2" in tmpl:
                icon = " "
            elif "\ue601" in tmpl:
                icon = " "
            return {
                "mod_name": "cmd_duration", "var_name": "$cmd_duration",
                "fg": fg or "white", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": icon, "raw_tmpl": "$duration",
                "options": options,
            }
        elif stype == "time":
            return {
                "mod_name": "time", "var_name": "$time",
                "fg": fg or "white", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": " ", "raw_tmpl": "$time",
                "options": options,
            }
        elif stype in ("battery",):
            return {
                "mod_name": "battery", "var_name": "$battery",
                "fg": fg or "white", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": "󰁹 ", "raw_tmpl": "$percentage",
                "options": options,
            }
        elif stype in ("sysinfo", "memory"):
            return {
                "mod_name": "memory_usage", "var_name": "$memory_usage",
                "fg": fg or "green", "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": "󰍛 ", "raw_tmpl": "$ram_pct",
                "options": options,
            }
        elif stype in runtime_map:
            m_name, v_name, ic, def_fg = runtime_map[stype]
            return {
                "mod_name": m_name, "var_name": v_name,
                "fg": fg or def_fg, "bg": bg,
                "leading": lead, "trailing": trail,
                "icon": ic, "raw_tmpl": "$version",
                "options": options,
            }

        return None

    def build_module_format(
        self,
        curr: Dict[str, Any],
        prev: Optional[Dict[str, Any]],
        next_seg: Optional[Dict[str, Any]],
        is_last: bool,
    ) -> Dict[str, Any]:
        mod_name = curr["mod_name"]
        bg = curr["bg"]
        fg = curr["fg"]
        icon = curr["icon"]
        raw_tmpl = curr["raw_tmpl"]

        # 1. Prefix: Transition from previous segment
        prefix = ""
        if prev and prev.get("bg") and bg:
            if prev["bg"] != bg:
                trans_sym = prev.get("trailing") or curr.get("leading") or ""
                prefix = f"[{trans_sym}](fg:{prev['bg']} bg:{bg})"
        elif curr.get("leading") and bg:
            prefix = f"[{curr['leading']}](fg:{bg})"

        # 2. Suffix: Transition to next segment or terminal boundary
        suffix = ""
        if is_last:
            end_sym = curr.get("trailing") or ""
            if bg and end_sym:
                suffix = f"[{end_sym}](fg:{bg}) "
        elif next_seg and not next_seg.get("bg") and bg:
            end_sym = curr.get("trailing") or ""
            suffix = f"[{end_sym}](fg:{bg}) "

        # 3. Assemble content format
        if bg:
            content_fmt = f"[ {icon}{raw_tmpl} ](fg:{fg} bg:{bg})"
        else:
            content_fmt = f"[{icon}{raw_tmpl}](fg:{fg}) "

        final_fmt = f"{prefix}{content_fmt}{suffix}"

        res: Dict[str, Any] = {"format": final_fmt}

        if mod_name == "directory":
            res["truncation_length"] = 3
            res["truncation_symbol"] = "…/"
        elif mod_name == "username":
            res["show_always"] = True
            if bg:
                res["format"] = f"{prefix}[{icon}$user ](fg:{fg} bg:{bg}){suffix}"
        elif mod_name == "cmd_duration":
            res["min_time"] = 1
        elif mod_name == "time":
            res["disabled"] = False
            raw_t_fmt = curr.get("options", {}).get("time_format", "15:04:05")
            res["time_format"] = convert_go_date_format(raw_t_fmt)
        elif mod_name == "git_branch":
            if bg:
                res["format"] = f"{prefix}[ {icon}$branch](fg:{fg} bg:{bg})"
                stat_suffix = suffix
                self.modules["git_status"] = {
                    "format": f"([$all_status$ahead_behind ](fg:{fg} bg:{bg})){stat_suffix}",
                    "modified": " ✎",
                    "staged": " ",
                    "stashed": " ",
                    "ahead": " ⇡${count}",
                    "behind": " ⇣${count}",
                    "diverged": " ⇕⇡${ahead_count}⇣${behind_count}",
                }
            else:
                res["format"] = f"[{icon}$branch]({fg}) "
                self.modules["git_status"] = {
                    "format": "([$all_status$ahead_behind](red) )",
                    "modified": " ✎",
                    "staged": " ",
                }

        return res

    def build_right_module_format(
        self,
        curr: Dict[str, Any],
        prev: Optional[Dict[str, Any]],
        next_seg: Optional[Dict[str, Any]],
        is_first: bool,
    ) -> Dict[str, Any]:
        bg = curr["bg"]
        fg = curr["fg"]
        icon = curr["icon"]
        raw_tmpl = curr["raw_tmpl"]

        prefix = ""
        if is_first and bg:
            # Inverted leading cap entering from terminal fill
            prefix = f"[](fg:{bg})"
        elif prev and prev.get("bg") and bg and prev["bg"] != bg:
            prefix = f"[](fg:{bg} bg:{prev['bg']})"

        if bg:
            fmt = f"{prefix}[ {icon}{raw_tmpl} ](fg:{fg} bg:{bg})"
        else:
            fmt = f"[ {icon}{raw_tmpl} ](fg:{fg})"

        res: Dict[str, Any] = {"format": fmt}
        if curr["mod_name"] == "time":
            res["disabled"] = False
            raw_t_fmt = curr.get("options", {}).get("time_format", "15:04:05")
            res["time_format"] = convert_go_date_format(raw_t_fmt)
        elif curr["mod_name"] == "battery":
            res["disabled"] = False

        return res

    def render_toml(
        self,
        left_mods: List[str],
        right_mods: List[str],
        line2_mods: List[str],
        is_single_line: bool,
    ) -> str:
        lines = [
            "# =====================================================================",
            f"# Nirmana-Shell - Transpiled Theme: {self.theme_name}",
            "# Ported from Oh My Posh JSON schema via Nirmana OMP Transpiler",
            "# =====================================================================",
            "",
            "scan_timeout = 30",
            "command_timeout = 1000",
            f"add_newline = {'false' if is_single_line else 'true'}",
            "",
        ]

        lines.append("format = \"\"\"")
        for m in left_mods:
            lines.append(f"{m}\\")

        if self.use_fill and right_mods:
            lines.append("$fill\\")
            for m in right_mods:
                lines.append(f"{m}\\")

        if line2_mods and not is_single_line:
            lines.append("$line_break\\")
            for m in line2_mods:
                lines.append(f"{m}\\")

        lines.append("\"\"\"")
        lines.append("")

        if self.use_fill and right_mods:
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


def main():
    parser = argparse.ArgumentParser(
        description="Transpile Oh My Posh theme JSON to Starship TOML for Nirmana-Shell."
    )
    parser.add_argument("input", help="Path to .omp.json file or HTTP/HTTPS URL")
    parser.add_argument("-o", "--output", help="Output path for .toml file")
    parser.add_argument("-n", "--name", help="Theme name identifier")
    parser.add_argument(
        "--no-fill", action="store_true", help="Disable Nirmana right-aligned $fill layout"
    )

    args = parser.parse_args()

    data, parsed_name = parse_omp_json(args.input)
    theme_name = args.name or parsed_name
    theme_name = re.sub(r"[^a-zA-Z0-9_\-]", "-", theme_name).strip("-")

    transpiler = OmpTranspiler(data, theme_name=theme_name, use_fill=not args.no_fill)
    toml_content = transpiler.transpile()

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path("themes") / f"{theme_name}.toml"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(toml_content, encoding="utf-8")
    print(f"Successfully transpiled Oh My Posh theme '{theme_name}' -> '{out_path}'")


if __name__ == "__main__":
    main()
