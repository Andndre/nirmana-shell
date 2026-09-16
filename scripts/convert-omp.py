#!/usr/bin/env python3
"""
Nirmana-Shell - Oh My Posh to Starship Theme Transpiler
Converts Oh My Posh theme JSON configurations (*.omp.json) into clean,
high-performance Starship themes (*.toml) aligned with Nirmana layout standards.
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


def convert_go_date_format(go_fmt: str) -> str:
    """Convert Go time reference format to strftime format."""
    res = go_fmt
    # Strip any inline OMP tags like <#fff>at</>, <#ffffff>...</>, <b>, etc.
    res = re.sub(r"<[^>]+>", "", res)

    for go_pat, strftime_pat in GO_DATE_TO_STRFTIME:
        res = re.sub(r"\b" + re.escape(go_pat) + r"\b", strftime_pat, res)
    return res


def clean_template_tags(template_str: str, current_bg: Optional[str] = None, palette: Optional[Dict[str, str]] = None) -> str:
    """Clean and translate OMP template tags into Starship format strings."""
    if not template_str:
        return ""

    palette = palette or {}

    def normalize_color(col: str) -> str:
        if not col or col == "transparent":
            return ""
        if col.startswith("p:"):
            key = col[2:]
            col = palette.get(key, key)
        else:
            col = palette.get(col, col)

        h = col[1:] if col.startswith("#") else col
        if len(h) == 3 and all(c in "0123456789abcdefABCDEF" for c in h):
            return f"#{h[0]*2}{h[1]*2}{h[2]*2}"
        elif len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h):
            return f"#{h}"
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

    # <#fg,#bg>text</>
    s = re.sub(r"<([^,>]+),([^>]+)>(.*?)</>", repl_fg_bg, template_str)
    # <#hex>text</> or <color_name>text</>
    s = re.sub(r"<#?([0-9a-fA-F]{3,6}|[a-zA-Z0-9_\-:]+)>(.*?)</>", repl_color, s)
    # Strip remaining XML-like tags (e.g. <b>, </b>, unclosed <#...>, </>)
    s = re.sub(r"<[^>]+>", "", s)
    return s


def parse_omp_json(source: str) -> Tuple[Dict[str, Any], str]:
    """Load JSON from local path, URL, or Oh My Posh theme name."""
    theme_name = ""
    url = source
    if not source.startswith("http://") and not source.startswith("https://"):
        path = Path(source)
        if not path.exists():
            # If neither local file nor full URL, try Oh My Posh official repository
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
            headers={"User-Agent": "Nirmana-Shell-Transpiler/1.0"},
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
        self.line1_left: List[str] = []
        self.line1_right: List[str] = []
        self.line2_modules: List[str] = []
        self.all_segments: List[Dict[str, Any]] = []

    def resolve_color(self, col: Optional[str]) -> Optional[str]:
        if not col or col == "transparent":
            return None
        # Handle OMP palette prefix "p:color_name"
        if col.startswith("p:"):
            key = col[2:]
            col = self.palette.get(key, key)
        elif col in self.palette:
            col = self.palette[col]

        h = col[1:] if col.startswith("#") else col
        if len(h) == 3 and all(c in "0123456789abcdefABCDEF" for c in h):
            return f"#{h[0]*2}{h[1]*2}{h[2]*2}"
        elif len(h) == 6 and all(c in "0123456789abcdefABCDEF" for c in h):
            return f"#{h}"
        return col

    def build_style(self, fg: Optional[str], bg: Optional[str]) -> str:
        fg = self.resolve_color(fg)
        bg = self.resolve_color(bg)
        parts = []
        if fg:
            parts.append(f"fg:{fg}" if bg else fg)
        if bg:
            parts.append(f"bg:{bg}")
        return " ".join(parts)

    def extract_segments(self):
        blocks = self.data.get("blocks", [])
        current_line = 1
        for block_idx, block in enumerate(blocks):
            alignment = block.get("alignment", "left")
            block_type = block.get("type", "prompt")
            is_rprompt = block_type == "rprompt" or alignment == "right"

            # In OMP, newline on block 0 is add_newline before prompt
            if block_idx > 0 and block.get("newline", False):
                current_line += 1

            for seg in block.get("segments", []):
                self.all_segments.append({
                    "seg": seg,
                    "is_right": is_rprompt,
                    "line": current_line,
                })

    def transpile(self) -> str:
        self.extract_segments()

        has_line2 = any(item["line"] >= 2 for item in self.all_segments)

        for item in self.all_segments:
            seg = item["seg"]
            is_right = item["is_right"]
            line = item["line"]

            res = self.process_segment(seg)
            if not res:
                continue

            mods = res if isinstance(res, list) else [res]
            for m in mods:
                if line >= 2:
                    if m not in self.line2_modules:
                        self.line2_modules.append(m)
                elif is_right:
                    if m not in self.line1_right:
                        self.line1_right.append(m)
                else:
                    if m not in self.line1_left:
                        self.line1_left.append(m)

        # Ensure directory is present somewhere
        if "$directory" not in self.line1_left and "$directory" not in self.line2_modules:
            self.line1_left.insert(0, "$directory")
            if "directory" not in self.modules:
                self.modules["directory"] = {
                    "format": "[$path](bold cyan) ",
                    "truncation_length": 3,
                    "truncation_symbol": "…/",
                }

        # Ensure git is present
        if "$git_branch" not in self.line1_left and "$git_branch" not in self.line2_modules:
            self.line1_left.append("$git_branch")
            self.line1_left.append("$git_status")
            if "git_branch" not in self.modules:
                self.modules["git_branch"] = {
                    "symbol": " ",
                    "format": "[$symbol$branch](bold purple) ",
                }
            if "git_status" not in self.modules:
                self.modules["git_status"] = {
                    "format": "([$all_status$ahead_behind](red) )",
                }

        # If prompt is single-line, make sure line 2 has character
        if not self.line2_modules:
            if "$character" in self.line1_left:
                self.line1_left.remove("$character")
            self.line2_modules.append("$character")
        elif "$character" not in self.line2_modules and "$character" not in self.line1_left:
            self.line2_modules.append("$character")

        if "character" not in self.modules:
            self.modules["character"] = {
                "success_symbol": "[❯](bold green) ",
                "error_symbol": "[❯](bold red) ",
            }

        return self.render_toml()

    def format_diamond(self, raw: str, bg: Optional[str], fg: Optional[str] = None, is_leading: bool = True) -> str:
        """Format leading/trailing diamond glyph, ensuring it is properly styled with colors."""
        if not raw:
            return ""

        if "<" in raw:
            cleaned = clean_template_tags(raw, current_bg=bg, palette=self.palette)
            if "[" in cleaned and "]" in cleaned and "(" in cleaned:
                return cleaned

            stripped = cleaned.strip()
            color = f"fg:{bg}" if bg else (f"fg:{fg}" if fg else None)
            if stripped and color:
                prefix = " " if raw.startswith(" ") else ""
                suffix = " " if raw.endswith(" ") else ""
                return f"{prefix}[{stripped}]({color}){suffix}"
            return cleaned

        stripped = raw.strip()
        if not stripped:
            return raw

        color = f"fg:{bg}" if bg else (f"fg:{fg}" if fg else None)
        if color:
            prefix = " " if raw.startswith(" ") else ""
            suffix = " " if raw.endswith(" ") else ""
            return f"{prefix}[{stripped}]({color}){suffix}"

        return raw

    def process_segment(self, seg: Dict[str, Any]) -> Optional[Union[str, List[str]]]:
        stype = seg.get("type", "")
        fg = self.resolve_color(seg.get("foreground", ""))
        bg = self.resolve_color(seg.get("background", ""))
        if not bg and "background_templates" in seg:
            for bt in seg["background_templates"]:
                m = re.search(r"(?:#([0-9a-fA-F]{3,6})|p:([a-zA-Z0-9_\-]+))", bt)
                if m:
                    if m.group(1):
                        bg = self.resolve_color(f"#{m.group(1)}")
                    elif m.group(2):
                        bg = self.resolve_color(f"p:{m.group(2)}")
                    if bg:
                        break

        if not fg and "foreground_templates" in seg:
            for ft in seg["foreground_templates"]:
                m = re.search(r"(?:#([0-9a-fA-F]{3,6})|p:([a-zA-Z0-9_\-]+))", ft)
                if m:
                    if m.group(1):
                        fg = self.resolve_color(f"#{m.group(1)}")
                    elif m.group(2):
                        fg = self.resolve_color(f"p:{m.group(2)}")
                    if fg:
                        break

        leading = seg.get("leading_diamond", "")
        trailing = seg.get("trailing_diamond", "")
        powerline_sym = seg.get("powerline_symbol", "")
        template = seg.get("template", "")
        options = seg.get("options") or seg.get("properties") or {}

        leading_fmt = self.format_diamond(leading, bg, fg=fg, is_leading=True)
        trailing_fmt = self.format_diamond(trailing or powerline_sym, bg, fg=fg, is_leading=False)

        if stype == "path":
            icon = " "
            if "\ue5ff" in template:
                icon = " "
            elif "\uea83" in template:
                icon = " "

            style_str = self.build_style(fg, bg)
            content = f"{icon}$path"
            if leading_fmt or trailing_fmt:
                fmt = f"{leading_fmt}[{content}]({style_str}){trailing_fmt} "
            elif bg:
                fmt = f"[](fg:{bg})[{content}]({style_str})[](fg:{bg}) "
            else:
                fmt = f"[{content}]({fg or 'cyan'}) "

            self.modules["directory"] = {
                "format": fmt,
                "truncation_length": 3,
                "truncation_symbol": "…/",
            }
            return "$directory"

        elif stype == "git":
            raw_branch_icon = options.get("branch_icon", "")
            branch_icon = re.sub(r"<[^>]+>", "", raw_branch_icon).strip()
            if not branch_icon:
                branch_icon = ""
            if "\ue725" in raw_branch_icon or "\ue725" in template:
                branch_icon = ""
            elif "\ue0a0" in raw_branch_icon or "\ue0a0" in template:
                branch_icon = ""
            branch_icon = f"{branch_icon} "
            style_str = self.build_style(fg, bg)

            if leading_fmt:
                branch_fmt = f"{leading_fmt}[{branch_icon}$branch]({style_str})"
            elif bg:
                branch_fmt = f"[](fg:{bg})[{branch_icon}$branch]({style_str})"
            else:
                branch_fmt = f"[{branch_icon}$branch]({fg or 'purple'})"

            self.modules["git_branch"] = {
                "format": branch_fmt,
            }

            status_style = style_str if bg else (fg or "purple")
            end_cap = trailing_fmt if trailing_fmt else (f"[](fg:{bg}) " if bg else " ")
            if end_cap and not end_cap.endswith(" "):
                end_cap = f"{end_cap} "
            self.modules["git_status"] = {
                "format": f"([$all_status$ahead_behind]({status_style}){end_cap})",
                "modified": " ",
                "staged": " ",
                "stashed": " ",
                "ahead": " ⇡${count}",
                "behind": " ⇣${count}",
                "diverged": " ⇕⇡${ahead_count}⇣${behind_count}",
            }
            return ["$git_branch", "$git_status"]

        elif stype == "session":
            style_str = self.build_style(fg, bg)
            user_icon = " " if "\ue200" in leading or "\ue200" in template else " "

            # Check if template has trailing connector like "<#ffffff>on</>"
            trailing_text = ""
            clean_tmpl = template.replace("SSHSession", "").replace("Session", "")
            if re.search(r">\s*on\s*<", template) or re.search(r"\b on \b", clean_tmpl):
                trailing_style = self.build_style("white", bg)
                trailing_text = f"[ on]({trailing_style})"

            if leading_fmt or trailing_fmt:
                fmt = f"{leading_fmt}[$user]({style_str}){trailing_text}{trailing_fmt} "
            elif bg:
                fmt = f"[](fg:{bg})[{user_icon}$user]({style_str})[](fg:{bg}) "
            else:
                fmt = f"[{user_icon}](#ff70a6)[$user]({fg or 'yellow'}){trailing_text} "

            self.modules["username"] = {
                "show_always": True,
                "format": fmt,
            }
            return "$username"

        elif stype == "time":
            raw_time_fmt = options.get("time_format", "15:04:05")
            strftime_fmt = convert_go_date_format(raw_time_fmt)
            style_str = self.build_style(fg, bg)

            if leading_fmt or trailing_fmt:
                leading_part = leading_fmt if leading_fmt else ""
                trailing_part = trailing_fmt if trailing_fmt else ""
                if trailing_part and not trailing_part.endswith(" "):
                    trailing_part = f"{trailing_part} "
                fmt = f"{leading_part}[ $time]({style_str}){trailing_part}"
            elif bg:
                fmt = f"[](fg:{bg})[ $time]({style_str})[](fg:{bg}) "
            else:
                fmt = f"[ $time]({fg or 'yellow'}) "

            self.modules["time"] = {
                "disabled": False,
                "time_format": strftime_fmt,
                "format": fmt,
            }
            return "$time"

        elif stype == "executiontime":
            style_str = self.build_style(fg, bg)
            icon = " "
            if "\ue601" in template:
                icon = " "
            elif "\ueba2" in template:
                icon = " "

            if leading_fmt or trailing_fmt:
                leading_part = leading_fmt if leading_fmt else (f"[](fg:{bg})" if bg else "")
                trailing_part = trailing_fmt if trailing_fmt else (f"[](fg:{bg})" if bg else "")
                if trailing_part and not trailing_part.endswith(" "):
                    trailing_part = f"{trailing_part} "
                fmt = f"{leading_part}[{icon}$duration]({style_str}){trailing_part}"
            elif bg:
                fmt = f"[](fg:{bg})[{icon}$duration]({style_str})[](fg:{bg}) "
            else:
                fmt = f"[{icon}$duration]({fg or 'yellow'}) "

            self.modules["cmd_duration"] = {
                "min_time": 1,
                "format": fmt,
            }
            return "$cmd_duration"

        elif stype in ("sysinfo", "memory"):
            style_str = self.build_style(fg, bg)
            if leading_fmt or trailing_fmt:
                fmt = f"{leading_fmt}[MEM: $ram_pct]({style_str}){trailing_fmt} "
            elif bg:
                fmt = f"[](fg:{bg})[󰍛 $ram_pct]({style_str})[](fg:{bg}) "
            else:
                fmt = f"[󰍛 $ram_pct]({fg or 'green'}) "

            self.modules["memory_usage"] = {
                "disabled": False,
                "threshold": 0,
                "format": fmt,
            }
            return "$memory_usage"

        elif stype == "battery":
            style_str = self.build_style(fg, bg)
            if leading_fmt or trailing_fmt:
                fmt = f"{leading_fmt}[$symbol$percentage]({style_str}){trailing_fmt} "
            elif bg:
                fmt = f"[](fg:{bg})[$symbol$percentage]({style_str})[](fg:{bg}) "
            else:
                fmt = f"[$symbol$percentage]({fg or 'green'}) "

            self.modules["battery"] = {
                "disabled": False,
                "format": fmt,
            }
            return "$battery"

        elif stype == "root":
            style_str = self.build_style(fg, bg)
            symbol = " " if "\uf0e7" in template else "⚡ "
            self.modules["sudo"] = {
                "disabled": False,
                "symbol": symbol,
                "format": f"[{symbol}]({fg or 'yellow'})",
            }
            return "$sudo"

        elif stype == "status":
            sym = " " if "\ue286" in template else (" " if "\ue23a" in template else ("⚡ " if "\uf0e7" in template else "❯ "))
            success_color = bg or fg or "green"
            err_color = "#ef5350"
            for t in seg.get("foreground_templates", []):
                m = re.search(r"#([0-9a-fA-F]{3,6})", t)
                if m:
                    raw_h = m.group(1)
                    if len(raw_h) == 3:
                        err_color = f"#{raw_h[0]*2}{raw_h[1]*2}{raw_h[2]*2}"
                    else:
                        err_color = f"#{raw_h}"

            self.modules["character"] = {
                "success_symbol": f"[{sym}](bold {success_color}) ",
                "error_symbol": f"[{sym}](bold {err_color}) ",
            }
            return "$character"

        # Runtimes mapping
        runtime_map = {
            "node": ("nodejs", "󰎙 ", fg or "#6CA35E", bg),
            "go": ("golang", " ", fg or "#8ED1F7", bg),
            "python": ("python", "󰌠 ", fg or "#FFDE57", bg),
            "rust": ("rust", " ", fg or "#DEA584", bg),
            "ruby": ("ruby", " ", fg or "#AE1401", bg),
            "java": ("java", " ", fg or "#ED8B00", bg),
            "dotnet": ("dotnet", "󰪮 ", fg or "#512BD4", bg),
            "php": ("php", " ", fg or "#777BB4", bg),
            "bun": ("bun", "󰎙 ", fg or "#FF9F43", bg),
            "dart": ("dart", " ", fg or "#7FD5EA", bg),
            "julia": ("julia", " ", fg or "#4063D8", bg),
            "aws": ("aws", " ", fg or "#FFA400", bg),
            "azure": ("azure", "󰠅 ", fg or "#0089D6", bg),
            "shell": ("shell", " ", fg or "#0077c2", bg),
            "package": ("package", "󰏗 ", fg or "#AEA4BF", bg),
        }

        if stype in runtime_map:
            mod_name, icon, r_fg, r_bg = runtime_map[stype]
            style_str = self.build_style(r_fg, r_bg)
            if leading_fmt or trailing_fmt:
                fmt = f"{leading_fmt}[{icon}$version]({style_str}){trailing_fmt} "
            elif r_bg:
                fmt = f"[](fg:{r_bg})[{icon}$version]({style_str})[](fg:{r_bg}) "
            else:
                fmt = f"[{icon}$version]({r_fg}) "

            if mod_name == "shell":
                self.modules[mod_name] = {
                    "disabled": False,
                    "format": fmt.replace("$version", "$indicator"),
                }
            else:
                self.modules[mod_name] = {
                    "symbol": icon,
                    "format": fmt,
                }
            return f"${mod_name}"

        return None

    def render_toml(self) -> str:
        lines = [
            "# =====================================================================",
            f"# Nirmana-Shell - Transpiled Theme: {self.theme_name}",
            "# Ported from Oh My Posh JSON schema via Nirmana OMP Transpiler",
            "# =====================================================================",
            "",
            "scan_timeout = 30",
            "command_timeout = 1000",
            "add_newline = true",
            "",
        ]

        lines.append("format = \"\"\"")
        for m in self.line1_left:
            lines.append(f"{m}\\")

        if self.use_fill and self.line1_right:
            lines.append("$fill\\")
            for m in self.line1_right:
                lines.append(f"{m}\\")

        if self.line2_modules:
            lines.append("$line_break\\")
            for m in self.line2_modules:
                lines.append(f"{m}\\")

        lines.append("\"\"\"")
        lines.append("")

        if self.use_fill and self.line1_right:
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
                    escaped = v.replace('"', '\\"')
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

