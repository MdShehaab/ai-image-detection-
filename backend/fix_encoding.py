# fix_encoding.py - Strip all non-cp1252 chars from train_v4.py and add utf-8 stdout reconfigure
import sys, os

path = os.path.join(os.path.dirname(__file__), "train_v4.py")
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Named replacements for common Unicode chars that appear in f-strings / comments
table = {
    "\u2705": "[OK]",   # green check
    "\u274c": "[X]",    # red cross
    "\u26a0": "[!]",    # warning
    "\u2139": "[i]",    # info
    "\u2208": "in",     # set membership (the original culprit)
    "\u2022": "*",      # bullet
    "\u2014": "--",     # em dash
    "\u2013": "-",      # en dash
    "\u2192": "->",     # right arrow
    "\u2265": ">=",
    "\u2264": "<=",
    "\u00d7": "x",      # times
    "\u221e": "inf",
    "\u2260": "!=",
    "\u00b1": "+/-",
    "\u2019": "'",
    "\u2018": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2500": "-",
    "\u2502": "|",
    "\u251c": "+",
    "\u2514": "+",
    "\u250c": "+",
    "\u2510": "+",
    "\u2518": "+",
    "\u2588": "#",
    "\u221a": "sqrt",
    "\u03b1": "alpha",
    "\u03b2": "beta",
    "\u2212": "-",
    "\u00b7": ".",
    "\u25b2": "^",
    "\u25bc": "v",
    "\u2714": "[OK]",
    "\u2716": "[X]",
    "\u2713": "[ok]",
    "\u2026": "...",
    "\u00b2": "^2",
    "\u00b3": "^3",
    "\u00b0": "deg",
}

for bad, good in table.items():
    if bad in content:
        n = content.count(bad)
        content = content.replace(bad, good)
        print(f"  U+{ord(bad):04X} -> {repr(good)}  ({n} occurrence(s))")

# Also strip Unicode variation selectors and other invisible modifiers
content = content.replace("\ufe0f", "")   # variation selector-16 (emoji modifier)
content = content.replace("\ufe0e", "")   # variation selector-15
content = content.replace("\u200b", "")   # zero-width space
content = content.replace("\u200c", "")   # zero-width non-joiner
content = content.replace("\u200d", "")   # zero-width joiner
content = content.replace("\ufeff", "")   # BOM

# Catch-all: any remaining char that cp1252 cannot encode
out = []
for ch in content:
    try:
        ch.encode("cp1252")
        out.append(ch)
    except UnicodeEncodeError:
        safe_msg = f"  Catch-all: U+{ord(ch):04X} -> '?'"
        sys.stdout.buffer.write((safe_msg + "\n").encode("utf-8"))
        out.append("?")
content = "".join(out)

# Add stdout UTF-8 reconfigure at the very top of the file (after module docstring)
# so any remaining Unicode in runtime strings still prints fine.
RECONFIGURE_BLOCK = (
    "\nimport sys as _sys\n"
    "if hasattr(_sys.stdout, 'reconfigure'):\n"
    "    try:\n"
    "        _sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
    "    except Exception:\n"
    "        pass\n"
    "del _sys\n"
)

# Insert right after the closing triple-quote of the module docstring
import re
content = re.sub(
    r'(""".*?""")',
    lambda m: m.group(0) + RECONFIGURE_BLOCK,
    content,
    count=1,
    flags=re.DOTALL,
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

try:
    content.encode("cp1252")
    print("\ncp1252 check: PASS -- no problematic chars remain in source")
except UnicodeEncodeError as e:
    print(f"\nSTILL HAS ISSUE: {e}")

print("Done.")
