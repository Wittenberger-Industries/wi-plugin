#!/usr/bin/env python3
"""
validate.py — pre-release check for the wi plugin. Run from anywhere:

    python3 scripts/validate.py

Checks (from the repo root, detected automatically):
  1. JSON validity of `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, and
     `.codex-plugin/plugin.json`; the Codex manifest declares name/version/skills and `skills` resolves.
  2. Every `skills/**/SKILL.md` / `agents/*.md` has valid YAML frontmatter with `name` + `description`
     — this catches the col-0 `<example>` / block-scalar bug that stopped the agents loading.
     Needs PyYAML for the full parse (`pip install pyyaml`); without it, the YAML parse is skipped
     and only delimiters + key presence are checked.
  3. Every `${CLAUDE_PLUGIN_ROOT}/<path>` reference in `.md` files resolves to a real file under the repo root.
  4. Cross-platform portability files exist (`references/{codex,copilot}-tools.md`, `AGENTS.md`) and the
     dev/research skills carry the Copilot Autopilot handoff branch.
  5. OKF conformance (see docs/specs/2026-06-14-okf-knowledge-format.md): every concept doc under
     skills/ · agents/ · references/ · docs/ plus README.md/AGENTS.md opens with parseable YAML
     frontmatter carrying a non-empty `type`. Each must also end with a trailing newline and have
     balanced code fences — the two signatures of a truncated/interrupted write (the bug class that
     shipped half-written docs before this guard existed). `index.md` / `log.md` are reserved and exempt.
  6. Generated-`.wi/`-file templates (the ```markdown blocks inside skills/agents that emit the runtime
     `.wi/` files) each open with frontmatter carrying a non-empty `type`, so a generated file can't ship
     type-less. Reserved `index.md`/`log.md` listings are exempt; console/shell examples (non-`markdown`
     fences) are skipped.

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
    ROOT / ".codex-plugin" / "plugin.json",
]
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

# 5. OKF conformance: every concept doc has parseable frontmatter + non-empty `type` --
RESERVED = {"index.md", "log.md"}  # OKF reserved filenames — exempt from the `type` rule
concept_md = (
    list(ROOT.glob("skills/**/*.md"))
    + list(ROOT.glob("agents/*.md"))
    + list(ROOT.glob("references/*.md"))
    + list(ROOT.glob("docs/**/*.md"))
    + [ROOT / "AGENTS.md", ROOT / "README.md"]
)
okf_checked = 0
for f in sorted(set(concept_md)):
    if not f.is_file() or f.name in RESERVED:
        continue
    okf_checked += 1
    rel = f.relative_to(ROOT)
    txt = f.read_text(encoding="utf-8")
    # Truncation guards: a concept doc cut off by an interrupted write ends mid-content. Two cheap
    # signatures catch it — no trailing newline, and an odd number of ``` fences (a block left open or a
    # stray close). validate.py is the only gate, so these prevent shipping a half-written doc.
    if txt and not txt.endswith("\n"):
        errors.append(f"{rel}: no trailing newline (truncated-write signature)")
    if sum(1 for ln in txt.splitlines() if ln.startswith("```")) % 2:
        errors.append(f"{rel}: unbalanced code fences (odd ``` count — truncated or stray fence)")
    if not txt.startswith("---"):
        errors.append(f"{rel}: OKF — no frontmatter (needs a non-empty 'type')")
        continue
    parts = txt.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{rel}: OKF — unterminated frontmatter")
        continue
    if HAVE_YAML:
        try:
            d = yaml.safe_load(parts[1])
        except Exception as e:
            errors.append(f"{rel}: OKF — frontmatter YAML error: {e}")
            continue
        if not isinstance(d, dict) or not d.get("type"):
            errors.append(f"{rel}: OKF — missing non-empty 'type'")
    elif "type:" not in parts[1]:
        errors.append(f"{rel}: OKF — missing 'type'")

# 6. Embedded generated-.wi/-file templates carry OKF `type` ---------------
# The generated .wi/ files live in user repos and never reach this script — but the *templates* that emit
# them are ```markdown blocks inside the skills/agents that write them. Guard those: every non-reserved
# generated-file template must open with frontmatter carrying a non-empty `type`, so a generated file can't
# ship type-less (the bug class: a bare `# Heading` template with no frontmatter, or frontmatter that
# forgot `type`). Reserved listings (index.md/log.md) are exempt — detected by the block's heading or the
# two prose lines just above it naming `index.md`/`log.md`. Console/shell examples use a non-`markdown`
# fence and are skipped.
fence_rx = re.compile(r"^([ \t]*)```([A-Za-z]*)[ \t]*$")
reserved_rx = re.compile(r"\b(?:index|log)\.md\b", re.I)
tmpl_files = sorted(set(ROOT.glob("skills/**/*.md")) | set(ROOT.glob("agents/*.md")))
tmpl_checked = 0
for f in tmpl_files:
    lines = f.read_text(encoding="utf-8").splitlines(keepends=True)
    rel = f.relative_to(ROOT)
    i = 0
    while i < len(lines):
        fmatch = fence_rx.match(lines[i])
        if not fmatch:
            i += 1
            continue
        indent, lang = fmatch.group(1), fmatch.group(2)
        open_ln = i + 1
        close_rx = re.compile(re.escape(indent) + r"```[ \t]*$")
        j = i + 1
        buf = []
        while j < len(lines) and not close_rx.match(lines[j]):
            buf.append(lines[j])
            j += 1
        nxt = j + 1  # past the closing fence (or EOF)
        if lang.lower() not in ("markdown", "md"):
            i = nxt
            continue
        body = "".join(ln[len(indent):] if ln.startswith(indent) else ln for ln in buf)
        first = next((ln for ln in body.splitlines() if ln.strip()), "")
        if not (first.lstrip().startswith("---") or first.lstrip().startswith("#")):
            i = nxt  # not a whole-file template (a prose/table snippet)
            continue
        if reserved_rx.search("".join(lines[max(0, i - 2):i]) + first):
            i = nxt  # reserved index.md / log.md listing — no frontmatter expected
            continue
        tmpl_checked += 1
        if not body.lstrip().startswith("---"):
            errors.append(f"{rel}: OKF template (line {open_ln}) — generated-file block has no frontmatter (needs a non-empty 'type')")
            i = nxt
            continue
        tparts = body.lstrip().split("---", 2)
        if len(tparts) < 3:
            errors.append(f"{rel}: OKF template (line {open_ln}) — unterminated frontmatter")
            i = nxt
            continue
        if HAVE_YAML:
            try:
                td = yaml.safe_load(tparts[1])
            except Exception as e:
                errors.append(f"{rel}: OKF template (line {open_ln}) — frontmatter YAML error: {e}")
                i = nxt
                continue
            if not isinstance(td, dict) or not td.get("type"):
                errors.append(f"{rel}: OKF template (line {open_ln}) — missing non-empty 'type'")
        elif "type:" not in tparts[1]:
            errors.append(f"{rel}: OKF template (line {open_ln}) — missing 'type'")
        i = nxt

# Report -------------------------------------------------------------------
note = "" if HAVE_YAML else "  [PyYAML absent → YAML parse skipped; `pip install pyyaml` for the full check]"
print(f"validate.py — {len(manifests)} manifest(s), {len(fm_files)} frontmatter file(s), "
      f"{okf_checked} OKF concept doc(s), {tmpl_checked} OKF template(s){note}")
if errors:
    print(f"\n[FAIL] {len(errors)} issue(s):")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("[OK] all checks passed")
sys.exit(0)
