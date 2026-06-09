#!/usr/bin/env python3
"""
validate.py — pre-release check for the wi plugin. Run from anywhere:

    python3 scripts/validate.py

Checks (from the repo root, detected automatically):
  1. JSON validity of `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json`.
  2. Every `skills/**/SKILL.md` / `agents/*.md` has valid YAML frontmatter with `name` + `description`
     — this catches the col-0 `<example>` / block-scalar bug that stopped the agents loading.
     Needs PyYAML for the full parse (`pip install pyyaml`); without it, the YAML parse is skipped
     and only delimiters + key presence are checked.
  3. Every `${CLAUDE_PLUGIN_ROOT}/<path>` reference in `.md` files resolves to a real file under the repo root.

Exit 0 if all pass; non-zero otherwise. Stdlib only (PyYAML optional).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repo root (holds .claude-plugin/)
errors = []

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

# 1. JSON manifests --------------------------------------------------------
manifests = [
    ROOT / ".claude-plugin" / "marketplace.json",
    ROOT / ".claude-plugin" / "plugin.json",
]
manifests.append(ROOT / ".codex-plugin" / "plugin.json")
for m in manifests:
    if not m.is_file():
        errors.append(f"missing manifest: {m.relative_to(ROOT)}")
        continue
    try:
        json.loads(m.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"invalid JSON {m.relative_to(ROOT)}: {e}")

# Codex manifest must declare name/version/skills, and skills must resolve
codex = ROOT / ".codex-plugin" / "plugin.json"
if codex.is_file():
    try:
        cd = json.loads(codex.read_text(encoding="utf-8"))
        for k in ("name", "version", "skills"):
            if not cd.get(k):
                errors.append(f".codex-plugin/plugin.json: missing '{k}'")
        skills_path = cd.get("skills", "")
        if skills_path and not (ROOT / skills_path).is_dir():
            errors.append(f".codex-plugin/plugin.json: skills path '{skills_path}' is not a dir")
    except Exception:
        pass  # JSON validity already reported by the loop above

# 2. Frontmatter on SKILL.md + agents -------------------------------------
fm_files = sorted(ROOT.glob("skills/**/SKILL.md")) + sorted(ROOT.glob("agents/*.md"))
for f in fm_files:
    txt = f.read_text(encoding="utf-8")
    rel = f.relative_to(ROOT)
    if not txt.startswith("---"):
        errors.append(f"{rel}: no frontmatter (must start with '---')")
        continue
    parts = txt.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{rel}: unterminated frontmatter")
        continue
    fm = parts[1]
    if HAVE_YAML:
        try:
            d = yaml.safe_load(fm)
        except Exception as e:
            errors.append(f"{rel}: frontmatter YAML error: {e}")
            continue
        if not isinstance(d, dict):
            errors.append(f"{rel}: frontmatter is not a mapping")
            continue
        for k in ("name", "description"):
            if not d.get(k):
                errors.append(f"{rel}: frontmatter missing '{k}'")
    else:
        for k in ("name:", "description:"):
            if k not in fm:
                errors.append(f"{rel}: frontmatter missing '{k.rstrip(':')}'")

# 3. ${CLAUDE_PLUGIN_ROOT} cross-refs resolve (against repo root) -----------
rx = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s`)\]]+)")
ref_md = (
    list(ROOT.glob("skills/**/*.md"))
    + list(ROOT.glob("agents/*.md"))
    + list(ROOT.glob("references/*.md"))
    + [ROOT / "AGENTS.md", ROOT / "README.md"]
)
for md in ref_md:
    if not md.is_file():
        continue
    for ref in rx.findall(md.read_text(encoding="utf-8")):
        if not (ROOT / ref).exists():
            errors.append(f"{md.relative_to(ROOT)}: broken ref ${{CLAUDE_PLUGIN_ROOT}}/{ref}")

for tm in ("references/codex-tools.md", "references/copilot-tools.md", "AGENTS.md"):
    if not (ROOT / tm).is_file():
        errors.append(f"missing portability file: {tm}")

for s in ("skills/dev/SKILL.md", "skills/research/SKILL.md"):
    if "autopilot" not in (ROOT / s).read_text(encoding="utf-8").lower():
        errors.append(f"{s}: missing Copilot Autopilot handoff branch")

# Report -------------------------------------------------------------------
note = "" if HAVE_YAML else "  [PyYAML absent → YAML parse skipped; `pip install pyyaml` for the full check]"
print(f"validate.py — {len(manifests)} manifest(s), {len(fm_files)} frontmatter file(s){note}")
if errors:
    print(f"\n[FAIL] {len(errors)} issue(s):")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("[OK] all checks passed")
sys.exit(0)
