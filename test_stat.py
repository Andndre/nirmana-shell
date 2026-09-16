import subprocess
from pathlib import Path

config = """format = \"$status\"

[status]
disabled = false
format = "[$symbol$status]($style) "
style = "fg:green"
symbol = "✔ "
"""

p = Path("test_stat.toml")
p.write_text(config, encoding="utf-8")

res0 = subprocess.run(["starship", "prompt", "-s", "0"], env={"STARSHIP_CONFIG": str(p)}, capture_output=True, text=True)
print("status 0:", repr(res0.stdout))

res1 = subprocess.run(["starship", "prompt", "-s", "1"], env={"STARSHIP_CONFIG": str(p)}, capture_output=True, text=True)
print("status 1:", repr(res1.stdout))

p.unlink(missing_ok=True)

