---
type: Plan
title: "#43 Grok Build as the fourth wi platform adapter"
description: "Add Grok Build (grok CLI, grok-4.5) as wi's fourth harness via the thin-adapter pattern: grok-tools.md capability map, a third (model-judged) keep-alive branch, models.md platform model resolution + xAI cross-provider, additive spine pointers, validate.py hard checks, and a blocking live recon spike + E2E gate. Additive-only to the Claude/Codex/Copilot branches."
feature: 43-grok-build-platform
timestamp: 2026-07-12
tags: [plan, portability, grok, platform, keep-alive, models]
---

# Grok Build platform adapter (#43) - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Grok Build (`grok` CLI, model `grok-4.5`) as wi's fourth first-class harness, using the established thin-adapter pattern, without changing any platform-neutral behavior.

**Architecture:** Same source skills; Grok is a fourth harness adapter. Packaging rides Grok's Claude-plugin compatibility. The autonomy spine is platform-conditional: Grok is Claude-compatible packaging + Copilot-class (model-judged) keep-alive + a first-class subagent/worktree CLI. All edits to existing platform branches are strictly additive (Claude/Codex/Copilot stay byte-stable).

**Tech Stack:** Markdown skill/reference prose; stdlib Python (`cross_review.py`, `validate.py`); pytest; JSON manifests.

## Design decisions (settled in brainstorming, 2026-07-12)

These are the decisions this plan encodes. They correct three over-fits in issue #43 itself, based on Grok's live recon of Grok Build `0.2.93` (`docs/plans/2026-07-12-grok-migration.md`). The authoritative design is `docs/specs/2026-07-12-grok-build-platform-design.md`; this plan is the task breakdown that executes it.

1. **Keep-alive is a THIRD branch, not the Claude/Codex predicate branch.** Grok's `/goal <objective>` completes when the agent self-marks `completed: true` via `update_goal` - model-judged, Copilot-class, not a hard predicate. We reuse the exact condition line as the *definition of done*, but document it as agent-judged with the unattended-run warning. This overrides the issue's "join the Claude/Codex `/goal` family" framing.
2. **`${CLAUDE_PLUGIN_ROOT}` resolution is a mandatory runtime protocol on Grok, not a docs note.** Grok only aliases the env var for hooks; it read empty in an interactive tool shell. wi shells out to `python ${CLAUDE_PLUGIN_ROOT}/skills/.../*.py`, so an unresolved var breaks execution. The adapter ships a resolve-once protocol and merge-gates on a real bundled-script run.
3. **`models.md` gets a platform/preset dimension (Option 2), scoped to routing only.** On a Grok host every dispatch is a Grok model, so the abstract tier tokens (`fable|opus|sonnet|haiku`) resolve through a per-host model map. Cross-provider diversity flips to OpenAI/Anthropic when the host is Grok (Grok reviewing Grok is same-family); the xAI cross-provider entry is for *other* hosts. This is the routing half only; MoA cross-vendor proposers stay postponed #34 and are out of scope here.
4. **Worktree policy: three distinct mechanisms, one canonical.** wi's feature worktree stays canonical; Grok session `-w` is an optional outer shell (never nested inside a wi feature worktree); subagent `isolation: worktree` is the level-2 escalate only, exactly like the existing Codex/shared-tree default.
5. **Subagent dispatch is inline, Codex-style.** `spawn_subagent` with the built-in `general-purpose` type carrying the `agents/wi-task-runner.md` contract inline; never depend on named-role registration.
6. **Scope of the merge gate: `scan` + `dev` end to end.** `rpa` is stretch (depends on the UiPath skill ecosystem + tenant auth), not a merge blocker.
7. **Implementation vehicle: hand-authored PR** following roadmap conventions, not `/wi:dev` dogfooding, because this PR modifies the platform/adapter layer itself. Single minor PR (1.11.1 -> 1.12.0).

---

## Global Constraints

Every task's requirements implicitly include this section. Values are copied verbatim from the repo's standing rules (`docs/roadmap.md` "Standing guardrails", the memory index).

- **Additive-only to existing platform branches.** The Claude/Codex `/goal` block and the Copilot Autopilot block in `references/keep-alive.md`, and `references/codex-tools.md` / `references/copilot-tools.md`, change only by *appending* a Grok block or leaving them untouched. `git diff main -- references/keep-alive.md references/codex-tools.md references/copilot-tools.md` shows no non-additive hunk in the Claude/Codex/Copilot regions. Any non-additive edit is a plan failure.
- **Never edit `agents/*.md`.** The agent charters are the most sensitive surface and no open issue may touch them (roadmap sequencing rule). The Grok dispatch recipe *references and inlines* `agents/wi-task-runner.md`; it never edits it.
- **Hotspot serialization.** This PR touches `skills/dev/SKILL.md` (a declared hotspot). No other branch may edit `skills/dev/SKILL.md`, `skills/ship/SKILL.md`, `skills/build/SKILL.md`, `references/wi-directory.md`, or `references/workflow.md` concurrently.
- **No em-dashes** in any shipped text, script, manifest, or the eventual PR body/commits. Use hyphen or comma forms. Machine-read markers use hyphen forms.
- **Citations** use `name:N` locators (`keep-alive:1`, `ship:8`) or quoted headings; never the section-sign symbol (validate.py bans U+00A7), never spelled-out "step/section N".
- **Bundled-script invocation uses `python`, never `python3`** (validate.py bans `python3 ${CLAUDE_PLUGIN_ROOT}`; the Windows Store `python3` stub is broken).
- **Every touched/new `.md` under skills/ agents/ references/ docs/** ends with a trailing newline and has balanced code fences (validate.py truncation guards), and opens with YAML frontmatter carrying a non-empty `type` (OKF).
- **New files only under `.gitignore`-whitelisted dirs.** `references/` and `docs/` are whitelisted; `references/grok-tools.md` is fine. Any new top-level path (e.g. `.grok-plugin/`) needs a `!/path` line in `.gitignore` or it silently vanishes.
- **Three-manifest version parity** (`.claude-plugin/plugin.json`, the `wi` entry in `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`), enforced by validate.py. If `.grok-plugin/plugin.json` is added, it joins the parity set and validate.py must check it (four-way).
- **Gate every task on** `python scripts/validate.py` exit 0 and `pytest tests/` green before its commit.

## Blocking spike inputs (measured in Task 0, consumed by later tasks)

Later tasks reference these by id. They are *measured facts*, gathered on a real Grok Build session in Task 0, not assumptions. Where a doc cell depends on one, it is marked `[from S-N]`.

- **S1** - env var outcome: `A` var set to plugin root / `B` empty in tool shell, set only in hooks / `C` never set.
- **S2** - does `export CLAUDE_PLUGIN_ROOT=...` persist across separate Grok shell tool calls? (yes/no)
- **S3** - exact install command + whether `--trust` and a post-install enable step are required.
- **S4** - exact entry-skill invocation form(s) that actually work (`/scan`, `/wi:scan`, `$scan`, natural language).
- **S5** - `/goal` fidelity: with a deliberately failed condition clause, does the agent still self-mark `completed: true`? (calibrates the warning's strength).
- **S6** - `grok models` output (confirm `grok-4.5` default + the cheap/fast id, expected `grok-composer-2.5-fast`).
- **S7** - does a named repo-agent dispatch resolve, or must the runner prompt be inlined into `general-purpose`?
- **S8** - `grok -w` session worktree vs a wi `git worktree add`: nesting/detached-HEAD behavior.

---

## Task 0: Blocking live recon spike (user-run on real Grok Build)

**This task gates the whole plan. Nothing merges until its results block is filled and Task 8's live E2E is green.** It runs on the owner's beta Grok Build session; it writes no repo code, only the measured results that later tasks consume. **Order matters: install/load first (that is itself under test), then the env + script gate, then the behavior probes.**

**Files:**
- Create: `docs/plans/2026-07-12-43-grok-spike-results.md` (measured answers; frozen record)

- [ ] **Step 1: Install, load, namespace, models (S3, S4, S6)**

```bash
grok plugin install Wittenberger-Industries/wi-plugin --trust   # confirm exact flags + whether --trust/enable are needed
grok inspect --json                                             # confirm wi skills/agents load
grok models                                                     # confirm model ids (expect grok-4.5, grok-composer-2.5-fast)
```

If the plugin path is itself the thing failing, fall back to a clone + `--plugin-dir` so Steps 2-3 can still run. Record S3 (command + trust + enable step), S4 (working slash form for scan/dev), S6 (model ids), and the **full tool-id list from `grok inspect`** (part of S7) so the `grok-tools.md` Tools table is filled from real ids: confirm the file write tool (`write` vs `create_file`), the edit tool (`search_replace`), the shell tool (`run_terminal_command`), and whether a fetch-style web tool (`web_fetch`) exists beside `web_search`.

- [ ] **Step 2: Confirm the plugin-root / script-execution reality (S1, S2)**

With wi loaded, from a skill/tool shell (not only the login shell):

```bash
echo "CLAUDE_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-<empty>}"
echo "GROK_PLUGIN_ROOT=${GROK_PLUGIN_ROOT:-<empty>}"
echo "PLUGIN_ROOT=${PLUGIN_ROOT:-<empty>}"
# resolve the wi root by hand if empty, then prove a bundled script runs:
python "<resolved-wi-root>/skills/ship/scripts/now.py"
# persistence-of-export check (S2):
export CLAUDE_PLUGIN_ROOT="<resolved-wi-root>"
# ...then in a SEPARATE shell tool call:
echo "persisted? ${CLAUDE_PLUGIN_ROOT:-<empty>}"
```

Record S1 (A/B/C) and S2 (yes/no).

- [ ] **Step 3: Prove agent-resolved script execution (the highest-value gate)**

Without the human pasting an absolute path into the prompt, ask the agent (in a fresh session, no prior "I resolved it for you" in context) to run:

```bash
python "<agent-resolved-root>/skills/ship/scripts/now.py"
python "<agent-resolved-root>/skills/scan/scripts/check_mermaid.py" <a tiny .mmd file>
```

Record: env empty or set; which resolution step worked; the absolute path used; both scripts exit 0.

- [ ] **Step 4: `/goal` fidelity + subagent + worktree (S5, S7, S8)**

- Arm a `/goal` with the wi condition line; confirm `status|pause|resume|clear`.
- Deliberately leave one condition clause unsatisfiable; observe whether the agent self-marks `completed: true` anyway. Record S5.
- Dispatch one `spawn_subagent` with `general-purpose`; separately try the named `wi-task-runner` agent. Record S7.
- Start `grok -w`, then attempt a wi `git worktree add -b wi/<slug> ...`; record nesting/detached-HEAD behavior (S8).

- [ ] **Step 5: Write and commit the results record**

Fill `docs/plans/2026-07-12-43-grok-spike-results.md` with S1-S8 and the two script exit codes.

```bash
git add docs/plans/2026-07-12-43-grok-spike-results.md
git commit -m "docs: Grok Build recon spike results (#43)"
```

**Merge gate from this task:** if S1 is B or C, Task 2's resolution protocol is mandatory (it is written that way regardless). If S2 is "no", Task 2 drops the `export` step as unreliable and mandates absolute-path-per-call.

---

## Task 1: models.md platform dimension + xAI cross-provider (code + TDD)

The one true code task. Adds per-host model resolution and xAI cross-provider normalization to `cross_review.py` (the only Python that parses `models.md`), plus the `models.md` prose that documents it.

**Files:**
- Modify: `skills/ship/scripts/cross_review.py`
- Modify: `references/models.md`
- Test: `tests/test_models_config.py`

**Interfaces:**
- Consumes: existing `parse_models_config(text) -> {preset, roles, cross_provider, overrides}` and `model_for(agent, cfg)`.
- Produces:
  - `parse_models_config` gains a `"platform_map"` key: `{host: {tier: model}}` parsed from a `## Platform model map` section (header columns = host names lowercased, e.g. `grok`; rows = tier -> model). Absent section -> `{}`.
  - `XAI_BASE = "https://api.x.ai/v1"` module constant.
  - `platform_model_for(agent, cfg, host="claude") -> str`: resolves `model_for(agent, cfg)`, then if `host != "claude"` and that tier is a key in `platform_map[host]`, returns the mapped model; otherwise returns the tier unchanged (Claude host, `inherit`, or an unmapped tier pass through verbatim).
  - xAI normalization: after parsing, if `cross_provider["provider"] == "xai"` and `base_url` is empty or still the OpenAI default, set it to `XAI_BASE`. The call dispatch treats `provider in ("openai", "xai")` as the OpenAI-shaped call (`_call_openai`), `"anthropic"` as `_call_anthropic`.

**Runtime dispatch path vs `platform_model_for` (read before implementing).** `cross_review.py` does **not** drive `spawn_subagent`; it is the cross-provider HTTP layer and the only Python that parses `models.md`. `platform_model_for` is therefore a **pure helper that encodes the map-resolution contract** (schema + the reference algorithm + test coverage), not the thing that "runs" routing. The actual runtime path is the orchestrator's, unchanged in shape from today's tier resolution: **detect host -> read the `## Platform model map` -> write the concrete per-role model ids into the `## Model routing (resolved)` block in `progress.md` -> pass those ids to `spawn_subagent`.** The prose in `references/models.md` (Step 5) states that path; `platform_model_for` is its executable, tested specification.

**Host detection rule (pin this in `models.md` prose):** the host is `grok` when the run is following `references/grok-tools.md` (i.e. wi was invoked under the `grok` CLI); otherwise the host is `claude` and the tier tokens are used as-is, exactly as today. Codex/Copilot are `claude`-tier hosts for this purpose unless they later get their own map column.

- [ ] **Step 1: Write failing tests for platform map + resolver**

Add to `tests/test_models_config.py`:

Use the EXACT table that ships in `references/models.md` as the fixture (golden test), so a drift between
the doc and the parser fails here:

```python
# Golden: byte-identical to the ## Platform model map table in references/models.md
GROK_PLATFORM_SECTION = """
## Platform model map
| Tier | grok |
|------|------|
| fable | grok-4.5 |
| opus | grok-4.5 |
| sonnet | grok-composer-2.5-fast |
| haiku | grok-composer-2.5-fast |
"""


class PlatformMapTest(unittest.TestCase):
    def test_platform_map_parsed(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG + GROK_PLATFORM_SECTION)
        self.assertEqual(cfg["platform_map"]["grok"]["opus"], "grok-4.5")
        self.assertEqual(cfg["platform_map"]["grok"]["sonnet"], "grok-composer-2.5-fast")

    def test_absent_platform_map_is_empty(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG)
        self.assertEqual(cfg["platform_map"], {})

    def test_claude_host_passes_tier_through(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG + GROK_PLATFORM_SECTION)
        # wi-task-runner role is sonnet; on the Claude host the tier is unchanged
        self.assertEqual(cross_review.platform_model_for("wi-task-runner", cfg, "claude"), "sonnet")

    def test_grok_host_maps_tier_to_model(self):
        cfg = cross_review.parse_models_config(FULL_CONFIG + GROK_PLATFORM_SECTION)
        self.assertEqual(cross_review.platform_model_for("wi-task-runner", cfg, "grok"), "grok-composer-2.5-fast")
        # wi-researcher has an override to haiku -> cheap Grok model
        self.assertEqual(cross_review.platform_model_for("wi-researcher", cfg, "grok"), "grok-composer-2.5-fast")

    def test_grok_host_unmapped_tier_passes_through(self):
        cfg = cross_review.parse_models_config(SIMPLE_CONFIG + GROK_PLATFORM_SECTION)
        # 'inherit' is not a mapped tier -> returned verbatim
        self.assertEqual(cross_review.platform_model_for("some-agent", cfg, "grok"), "inherit")


XAI_CONFIG = """---
preset: custom
---
## Cross-provider config
| Key | Value |
|-----|-------|
| provider | xai |
| model | grok-4.5 |
| api_key_env | XAI_API_KEY |
"""


class XaiProviderTest(unittest.TestCase):
    def test_xai_defaults_base_url_when_unset(self):
        # No base_url row -> parser pre-fills the OpenAI default -> normalization swaps in XAI_BASE.
        cfg = cross_review.parse_models_config(XAI_CONFIG)
        self.assertEqual(cfg["cross_provider"]["provider"], "xai")
        self.assertEqual(cfg["cross_provider"]["base_url"], cross_review.XAI_BASE)
        self.assertTrue(cross_review.cross_provider_configured(cfg))

    def test_xai_respects_explicit_base_url(self):
        cfg = cross_review.parse_models_config(
            XAI_CONFIG + "| base_url | https://custom.example/v1 |\n"
        )
        self.assertEqual(cfg["cross_provider"]["base_url"], "https://custom.example/v1")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_models_config.py -q`
Expected: FAIL (`AttributeError: module 'cross_review' has no attribute 'platform_model_for'` / KeyError `platform_map`).

- [ ] **Step 3: Implement in `cross_review.py`**

Add the constant near `PROVIDER_DEFAULTS`:

```python
XAI_BASE = "https://api.x.ai/v1"
```

In `parse_models_config`, after the `overrides` loop and before the `return`, add platform-map parsing and xAI normalization. Parse contract: the section is a single pipe table whose **first non-separator row is the header** (`| Tier | <host> ... |`, col 0 label ignored, cols 1+ are host names); every later row maps one tier to that host's model. This does not reuse `_parse_table` (which drops the header we need):

```python
    # Platform model map: first non-separator row names the hosts; each later row maps a tier.
    platform_map = {}
    pm_lines = [ln.strip() for ln in _section(body, "Platform model map") if ln.strip().startswith("|")]
    pm_lines = [ln for ln in pm_lines if set(ln.strip("|")) - {"-", " ", ":"}]  # drop separator rows
    if pm_lines:
        header = [c.strip().lower() for c in pm_lines[0].strip("|").split("|")]
        for ln in pm_lines[1:]:
            cells = [c.strip("*` ") for c in ln.strip("|").split("|")]
            tier = cells[0]
            for col in range(1, len(header)):
                if col < len(cells) and cells[col]:
                    platform_map.setdefault(header[col], {})[tier] = cells[col]

    if provider.get("provider") == "xai" and provider.get("base_url") in ("", PROVIDER_DEFAULTS["base_url"]):
        provider["base_url"] = XAI_BASE
```

Add `"platform_map": platform_map,` to the returned dict.

Add the resolver next to `model_for`:

```python
def platform_model_for(agent, cfg, host="claude"):
    """Concrete model for a wi-dispatched agent on a given host.

    Claude host (or absent map): the tier token is the model. Non-Claude host: map the
    tier through the `## Platform model map` for that host; an unmapped tier (or `inherit`)
    passes through verbatim.
    """
    tier = model_for(agent, cfg)
    if host == "claude" or not cfg:
        return tier
    return cfg.get("platform_map", {}).get(host, {}).get(tier, tier)
```

Update the call dispatch in `run_review`:

```python
    call = _call_anthropic if provider["provider"] == "anthropic" else _call_openai
```

stays as-is (xai already falls to `_call_openai`); add a clarifying comment `# openai + xai (OpenAI-compatible) share the chat/completions shape; anthropic uses /v1/messages`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_models_config.py -q`
Expected: PASS (all new + existing tests).

- [ ] **Step 5: Add the `models.md` prose (Option 2 schema)**

In `references/models.md`, add a `## Platform model resolution` section after "The config file" section (before "Presets"), and extend the config template with the new section. Exact content to add:

````markdown
## Platform model resolution (non-Claude hosts)

The Roles-table tokens (`fable | opus | sonnet | haiku`) are the **canonical routing tiers**, defined on
Claude. On a **non-Claude host** every dispatch runs that host's own models, so the resolve-once step maps
each tier to a concrete host model through an optional `## Platform model map`:

```markdown
## Platform model map
| Tier | grok |
|------|------|
| fable | grok-4.5 |
| opus | grok-4.5 |
| sonnet | grok-composer-2.5-fast |
| haiku | grok-composer-2.5-fast |
```

- Columns are host names (`grok`); rows map a canonical tier to that host's model id (resolved from
  `grok models` at config time: `grok-4.5` is the strong/default model, `grok-composer-2.5-fast` the
  cheap/fast one). An unmapped tier, or `inherit`, passes through unchanged.
- The `## Model routing (resolved)` block records the concrete per-role model for the running host: a
  Grok model id on a Grok host, the Claude tier token on Claude. `orchestrator` stays informational (the
  session model, set by the host's own model selector).
- **Cross-provider diversity on a Grok host:** point the cross-provider layer at `openai` or `anthropic`,
  not `xai` (a Grok host reviewing with a Grok model is same-family, which defeats the diversity purpose).
  The `provider: xai` entry below is for the *other* hosts.
- The map is optional: absent it, non-Claude hosts run every dispatch at the session model (`inherit`
  behavior), same as today.
````

Then extend the `## Cross-provider config` documentation (the provider row values) to note xAI:

````markdown
The cross-provider `provider` accepts `openai | anthropic | xai | none`. `xai` uses xAI's
OpenAI-compatible endpoint: set `model` (e.g. `grok-4.5`) and `api_key_env` (`XAI_API_KEY`); `base_url`
defaults to `https://api.x.ai/v1` when unset.
````

- [ ] **Step 6: Validate and commit**

Run: `python scripts/validate.py` (expect `[OK]`) and `python -m pytest tests/ -q` (expect all pass).

```bash
git add skills/ship/scripts/cross_review.py references/models.md tests/test_models_config.py
git commit -m "feat: platform model resolution + xAI cross-provider in models.md (#43)"
```

---

## Task 2: references/grok-tools.md (the capability map)

New portability reference mirroring `codex-tools.md` / `copilot-tools.md`, plus the mandatory root-resolution protocol.

**Files:**
- Create: `references/grok-tools.md`

- [ ] **Step 1: Write the file**

Content (fill the `[from S-N]` cells from Task 0's results; everything else is final):

````markdown
---
type: Reference
title: "Grok Build: tool & capability mapping for wi"
description: Claude Code to Grok Build (grok CLI) tool-name and capability equivalents used when running wi on Grok, plus the mandatory plugin-root resolution protocol.
timestamp: 2026-07-12
tags: [grok, tools, portability, reference]
---

# Grok Build: tool & capability mapping for wi

wi's skills are written with Claude Code names. On Grok Build (`grok` CLI), use these equivalents.

## ${CLAUDE_PLUGIN_ROOT}: resolve once, then use an absolute path (mandatory)

`${CLAUDE_PLUGIN_ROOT}` means the **wi plugin root**: the directory holding `skills/`, `agents/`, and
`.claude-plugin/`. Grok aliases the env var for hooks only, and it can be empty in a tool shell
[from S1], so wi must resolve it, not rely on the variable:

1. Resolve **once** at the start of any wi entry skill (scan / dev / rpa), before the first
   `${CLAUDE_PLUGIN_ROOT}` script call.
2. **Never pass an unexpanded `${CLAUDE_PLUGIN_ROOT}` into the shell.** Resolution order:
   1. `$CLAUDE_PLUGIN_ROOT` if non-empty and it contains `skills/` + `.claude-plugin/`.
   2. `$GROK_PLUGIN_ROOT` / `$PLUGIN_ROOT` if they look like the wi root.
   3. The loaded wi plugin path from `grok inspect` / plugin list.
   4. Walk up from cwd for a dir holding both `skills/scan/SKILL.md` and `.claude-plugin/plugin.json`
      (clone / `--plugin-dir`).
3. Use that **absolute path** in every `python <root>/skills/.../*.py` call for the rest of the run.
   [from S2: if `export` does not persist across shell calls, absolute-path-per-call is the only
   guarantee; if it does, `export CLAUDE_PLUGIN_ROOT=<resolved>` once is a convenience.]

This is the same root rule Copilot uses (`references/copilot-tools.md` "${CLAUDE_PLUGIN_ROOT}"), made a
hard protocol because Grok shells out. The script-invocation fallback is `references/workflow.md`
"Script invocation".

## Install & enable

`grok plugin install Wittenberger-Industries/wi-plugin --trust` [from S3], then enable if plugins are
disabled by default. Grok loads Claude marketplace plugins (skills, agents, hooks, `AGENTS.md`) with zero
config; the clone + plugin-dir path is the fallback. Publishing to the official catalog is a separate PR
to `xai-org/plugin-marketplace`.

## Tools
**Provisional: verify every id against `grok inspect` on the spike (S3/S7) before this file ships.** The
`?`-flagged rows are the ones most likely to differ across Grok Build versions.
| wi/skill says | Grok equivalent (confirm on spike) |
|---|---|
| Read a file | `read_file` |
| Write / create a file | `write` (some builds `create_file`) ? |
| Edit a file | `search_replace` |
| Bash / run a command | `run_terminal_command` |
| Grep / Glob | `grep` / file search (`run_terminal_command` with `rg`/`grep`/`find`) |
| dispatch a subagent / task-runner | `spawn_subagent` (built-in types `general-purpose | explore | plan`, depth limit 1; `isolation`, `background`, `capability_mode` optional) |
| parallel waves | multiple `spawn_subagent` calls in one turn; inline the runner/researcher prompt (do not rely on named-role dispatch) |
| TodoWrite | `todo_write` |
| WebSearch | `web_search` |
| WebFetch | `web_fetch` or the build's fetch-style tool, if present; else `web_search` with a URL ? |
| invoke a wi skill | skills load natively: `/scan`, `/dev`, `/rpa` [from S4] (qualified `/wi:scan` if a name collides), or natural-language auto-trigger; flat `wi-*` aliases give a one-token form once scan's bootstrap installs them |
| resolve a skill's `SKILL.md` path (dispatch pointer for pinned runners) | it is under the skill's install dir (the resolved wi root's `skills/<skill>/SKILL.md`, or `~/.agents/skills/<skill>/SKILL.md` for flat aliases); the orchestrator resolves it once and passes it in the `[frontend]`-style dispatch |

## Subagent dispatch (inline, Codex-style)
Grok's tool is `spawn_subagent`. Dispatch each wi role as `general-purpose` with the role's contract
inlined into the prompt; do **not** assume the named `wi-task-runner` agent resolves [from S7]:

| wi role | Grok dispatch |
|---------|----------------|
| `wi-task-runner` | `general-purpose`, prompt = inlined `agents/wi-task-runner.md` contract + task skeleton; **shared** feature worktree (`isolation: none`) |
| `wi-researcher` | `explore` or `general-purpose` + read-only; inline researcher contract |
| `wi-code-checker` | `general-purpose`; inline checker contract |

## Worktrees (three mechanisms, one canonical)
- **wi feature worktree** (`git worktree add -b wi/<slug> ...`) is canonical; the orchestrator is the sole
  committer (`skills/build/references/worktrees-and-subagents.md`).
- **Grok session `-w`** is an optional outer shell; do **not** nest a wi feature worktree inside it
  [from S8]. If already inside a session worktree (detached HEAD / linked worktree), follow the sandboxed
  variant in `worktrees-and-subagents.md`: commit in place, hand the user branch + PR text.
- **Subagent `isolation: worktree`** is the level-2 escalate only (file collision / non-parallel-safe
  tests), matching the existing escalation ladder.

## Keep-alive
Grok's `/goal` is **model-judged**, not a hard predicate: see the Grok Build branch in
`references/keep-alive.md`. Reuse the condition line as the definition of done; the unattended warning
applies.

## Models & usage
`grok models` lists ids (`grok-4.5` default, `grok-composer-2.5-fast` fast) [from S6]; pass the model on
`spawn_subagent` / session per `references/models.md` "Platform model resolution". Usage: `/usage`
(`token_report.py`'s Claude transcript parse does not apply; duration comes from wi's own stamps, same as
Copilot's ledger note).

## Permissions (unattended)
`--always-approve` / `--yolo` and headless `-p` / `--max-turns` / `--continue` run Grok unattended; the
same unattended warning as Copilot applies. `--check` (headless self-verification) is optional and is not
wi's keep-alive.
````

- [ ] **Step 2: Validate and commit**

Run: `python scripts/validate.py` (expect `[OK]`; note it now expects this file after Task 5, so this run just confirms no OKF/truncation/ref errors).

```bash
git add references/grok-tools.md
git commit -m "docs: references/grok-tools.md capability map for Grok Build (#43)"
```

---

## Task 3: keep-alive.md third branch (Grok, model-judged)

Additive third bullet; Claude/Codex and Copilot blocks untouched.

**Files:**
- Modify: `references/keep-alive.md`

- [ ] **Step 1: Add the Grok bullet after the Copilot block**

Insert after the Copilot Autopilot block (after `references/keep-alive.md:46`, before the closing paragraph at `keep-alive:48`):

````markdown
- **Grok Build** (native `/goal`, but **model-judged**, not a predicate):

  ```
  /goal The <slug> PR is open with its remote checks green (or none configured) and its branch passes <lint + test commands from repo-map.md>; .wi/features/<slug>/progress.md Phase is done. Constraints: only files named in tasks.md change; never force-push; tests are never weakened to pass.
  ```

  Grok drives the goal itself and marks it complete via `update_goal` when **it** judges the work done, so
  the condition line is the **definition of done**, not a platform predicate the runtime enforces. Paste it
  as one line. Use `/goal pause | resume` around auth-gate stops. Headless fallback:
  `grok -p "<prompt incl. the done-condition>" --always-approve --max-turns <N>` with `--continue` /
  session resume.

  ⚠️ Because completion is model-judged (and `--always-approve` runs Grok unattended: prompts suppressed),
  the agent can self-complete before remote checks are green or `progress.md` Phase is `done`. Treat this
  as Copilot-class autonomy: use it in repos you trust, and do not assume the runtime blocks on the
  condition the way Claude/Codex `/goal` does.
````

Update the file's closing pointer line (`keep-alive:48-49`) additively so it names Grok:

- Old: `... lives in `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md` / `copilot-tools.md`.`
- New: `... lives in `${CLAUDE_PLUGIN_ROOT}/references/codex-tools.md` / `copilot-tools.md` / `grok-tools.md`.`

Also update the frontmatter `description` additively to mention the Grok branch (keep under any cap; this is a reference, no SKILL cap applies).

- [ ] **Step 2: Verify byte-stability of the other branches**

Run:
```bash
git diff main -- references/keep-alive.md
```
Expected: only added lines (the Grok bullet + the two additive pointer edits). The Claude/Codex `/goal` code fence and the Copilot Autopilot code fence show zero changed lines.

- [ ] **Step 3: Validate and commit**

Run: `python scripts/validate.py` (expect `[OK]`).

```bash
git add references/keep-alive.md
git commit -m "docs: Grok Build keep-alive branch (model-judged /goal) (#43)"
```

---

## Task 4: Spine pointers (AGENTS.md, dev, research, build ref, bootstrap)

All additive: each file names Grok beside the existing platforms and points at `grok-tools.md`.

**Files:**
- Modify: `AGENTS.md`
- Modify: `skills/dev/SKILL.md`
- Modify: `skills/research/SKILL.md`
- Modify: `skills/build/references/worktrees-and-subagents.md`
- Modify: `skills/scan/references/plugin-bootstrap.md`

- [ ] **Step 1: AGENTS.md**

- Frontmatter `description` and `tags`: add `grok` additively.
- In "If you are not Claude Code" list (`AGENTS.md:20-23`), add a bullet:
  `- **Grok Build:** references/grok-tools.md`
- In "Invoking wi" persistence line (`AGENTS.md:38-39`), extend additively:
  `Claude/Codex use built-in /goal; Grok Build uses its native (model-judged) /goal; Copilot uses Autopilot flags (see the tool map).`

- [ ] **Step 2: skills/dev/SKILL.md (additive)**

- `dev/SKILL.md:17-18`: extend the keep-alive sentence additively: `/goal on Claude Code & Codex, Grok Build's model-judged /goal, Autopilot on Copilot.`
- `dev/SKILL.md:70-72`: extend the mechanism pointer additively: add `/ grok-tools.md` to the `codex-tools.md / copilot-tools.md` reference, and add `, Grok Build's model-judged /goal` to the parenthetical listing the templates. Keep `autopilot` present (validate.py check 4 still needs it).

- [ ] **Step 3: skills/research/SKILL.md (additive)**

- `research/SKILL.md:164-165`: extend the templates parenthetical additively to name Grok Build's model-judged `/goal` beside Claude/Codex and Copilot. Keep `autopilot` present.

- [ ] **Step 4: skills/build/references/worktrees-and-subagents.md (additive)**

- In "Subagent dispatch" (`worktrees-and-subagents.md:72-79`), add Grok to the platform list: `... Codex uses spawn_agent ...; Grok Build uses spawn_subagent (general-purpose, prompt inline; see references/grok-tools.md).`
- In the sandboxed-worktree variant (`worktrees-and-subagents.md:57-61`), add one line: Grok session `-w` worktrees are an optional outer shell; do not nest a wi feature worktree inside one; subagent `isolation: worktree` is the level-2 escalate only.

- [ ] **Step 5: skills/scan/references/plugin-bootstrap.md (additive)**

- In "Entry-command aliases" (`plugin-bootstrap.md:31-43`), add Grok: on Grok the entry points invoke as `/scan`, `/dev`, `/rpa` (or `/wi:scan` when qualified); the flat `wi-*` aliases copy into `~/.agents/skills/` (and/or Grok's skills dir) the same way.
- In "Recommended set" note that superpowers is available on Grok's marketplace too.

- [ ] **Step 6: Validate byte-stability + commit**

Run: `python scripts/validate.py` (expect `[OK]`). Confirm each diff is additive (no reworded Claude/Codex/Copilot clauses).

```bash
git add AGENTS.md skills/dev/SKILL.md skills/research/SKILL.md skills/build/references/worktrees-and-subagents.md skills/scan/references/plugin-bootstrap.md
git commit -m "docs: spine pointers name Grok Build beside the other harnesses (#43)"
```

---

## Task 5: validate.py extensions (hard checks)

Extend, never weaken. Grok's presence is asserted the same style as the existing Copilot Autopilot check.

**Files:**
- Modify: `scripts/validate.py`
- Test: `tests/test_timing_report.py` is unrelated; add a dedicated check by running validate.py against the tree (no new pytest needed, but confirm exit 0).

- [ ] **Step 1: Require the Grok portability file**

In the portability-files loop (`validate.py:149-151`), add `references/grok-tools.md`:

```python
for tm in ("references/codex-tools.md", "references/copilot-tools.md", "references/grok-tools.md", "AGENTS.md"):
```

- [ ] **Step 2: Require the Grok keep-alive marker**

After the Copilot Autopilot check (`validate.py:153-155`), add a keep-alive marker check:

```python
ka = (ROOT / "references/keep-alive.md").read_text(encoding="utf-8")
if "Grok Build" not in ka or "update_goal" not in ka:
    errors.append("references/keep-alive.md: missing the Grok Build model-judged /goal branch")
```

- [ ] **Step 3: Require the Grok handoff pointer in dev/research**

Extend the dev/research loop (`validate.py:153-155`) so each file also mentions Grok:

```python
for s in ("skills/dev/SKILL.md", "skills/research/SKILL.md"):
    body = (ROOT / s).read_text(encoding="utf-8").lower()
    if "autopilot" not in body:
        errors.append(f"{s}: missing Copilot Autopilot handoff branch")
    if "grok" not in body:
        errors.append(f"{s}: missing Grok Build handoff pointer")
```

- [ ] **Step 4: (Deferred) four-way manifest parity**

Only if Task 7 adds `.grok-plugin/plugin.json`: extend the manifest list (`validate.py:58-62`) and the parity set (`validate.py:86-96`) to include it. If `.grok-plugin/` is not added, leave manifest checks unchanged (three-way).

- [ ] **Step 5: Update the docstring**

Update `validate.py`'s check-4 docstring (`validate.py:17-18`) to say `references/{codex,copilot,grok}-tools.md` and note the keep-alive Grok marker + dev/research Grok pointer.

- [ ] **Step 6: Run and commit**

Run: `python scripts/validate.py` (expect `[OK]`) and `python -m pytest tests/ -q` (expect all pass).

```bash
git add scripts/validate.py
git commit -m "test: validate.py requires grok-tools + keep-alive/dev/research Grok markers (#43)"
```

---

## Task 6: README platform matrix + install

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a Grok column to the matrix**

Add a fourth column to the table (`README.md:60-66`). New header + rows:

```markdown
| | Claude Code | Codex CLI | Copilot CLI | Grok Build |
|---|---|---|---|---|
| Skills | plugin (`.claude-plugin/`) | `.codex-plugin/` (+ reads `.claude-plugin/marketplace.json`) | `plugin install` (reads `.claude-plugin/`); fallback whole-repo `/skills add` | `grok plugin install --trust` (reads `.claude-plugin/`); enable if disabled |
| Keep-alive | built-in `/goal` | native `/goal` | Autopilot flags | native `/goal` (model-judged) |
| Command namespace | `/wi:dev` | `$wi-dev` (alias) / `$dev` | `/wi-dev` (alias) / `/wi dev` | `/dev` (or `/wi:dev`) / `wi-dev` (alias) |
| `${CLAUDE_PLUGIN_ROOT}` | native | compat var | the installed plugin root (or the clone) | resolve to the plugin root (env var is hook-only) |
| Subagents | Agent/Task | `spawn_agent` | `task` / `/fleet` | `spawn_subagent` (general-purpose, inline) |
```

- Intro line (`README.md:11-12`) and the description at `README.md:4`: add Grok Build additively.
- Tool-map pointer (`README.md:68`): add `and references/grok-tools.md`.
- Add a `**Grok Build**:` install stanza after the Copilot stanza (`README.md:54`), mirroring the others: install command, namespace note, the model-judged keep-alive caveat pointing at `references/keep-alive.md`.

- [ ] **Step 2: Validate and commit**

Run: `python scripts/validate.py` (expect `[OK]`).

```bash
git add README.md
git commit -m "docs: README documents Grok Build as the fourth harness (#43)"
```

---

## Task 7: Manifests version bump (+ optional .grok-plugin)

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.codex-plugin/plugin.json`
- Create (only if S3/Task 8 proves it is needed): `.grok-plugin/plugin.json` + `.gitignore` whitelist line

- [ ] **Step 1: Bump all three versions together to 1.12.0**

Set `version` to `1.12.0` in `.claude-plugin/plugin.json`, the `wi` entry of `.claude-plugin/marketplace.json`, and `.codex-plugin/plugin.json`. Keep them identical (validate.py parity).

- [ ] **Step 2: Mention Grok in the three descriptions**

In each manifest `description`, change "for Claude Code, Codex CLI, and Copilot CLI" to include Grok Build. Update the keep-alive parenthetical to a form that does NOT conflate Grok's model-judged goal with Claude's predicate: e.g. `(Claude/Codex predicate /goal; Grok model-judged /goal; Copilot Autopilot)`. No em-dashes.

- [ ] **Step 3: `.grok-plugin/plugin.json` only if the live install requires it**

If Task 8 shows Grok does not load wi via the Claude-plugin layout alone, add `.grok-plugin/plugin.json` (mirror `.codex-plugin/plugin.json`: `name`, `version` 1.12.0, `skills: "./skills/"`), add `!/.grok-plugin/` to `.gitignore`, and extend validate.py to four-way parity (Task 5 Step 4). Otherwise skip this step and record "defer .grok-plugin" in the PR.

- [ ] **Step 4: Validate and commit**

Run: `python scripts/validate.py` (expect `[OK]`; parity check green).

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json
git commit -m "chore: bump wi to 1.12.0 (Grok Build platform) (#43)"
```

---

## Task 8: Live E2E validation gate (user-run on real Grok Build)

**Merge gate. All four sub-gates must be green before the PR merges.** Runs on the owner's Grok session against the branch.

- [ ] **Step 1: Install + load**

`grok plugin install <branch or path> --trust` (+ enable); `grok inspect --json` shows wi skills + agents.

- [ ] **Step 2: Script-execution gate (from Task 0, now against the branch)**

Agent resolves the plugin root and runs `python <root>/skills/ship/scripts/now.py` and `check_mermaid.py` with no human-pasted absolute path, in a fresh session. Both exit 0.

- [ ] **Step 3: scan + dev end to end**

Invoke the documented entry form for `scan`, then `dev` on a tiny feature; arm the Grok keep-alive line; observe at least one parallel `spawn_subagent` wave in the feature worktree (no nested session worktree); reach an open PR (or the local close-out on a remote-less repo).

- [ ] **Step 4: Byte-stability + static gates**

`python scripts/validate.py` exits 0; `python -m pytest tests/ -q` green;
`git diff main -- references/codex-tools.md references/copilot-tools.md` is empty;
`git diff main -- references/keep-alive.md` shows only additive hunks.

- [ ] **Step 5: Fill the open-questions checklist with measured answers**

Update `docs/plans/2026-07-12-43-grok-spike-results.md` with the E2E outcomes (including the honest `/goal` fidelity result from S5, e.g. "predicate not enforced; model-judged"). Commit.

- [ ] **Step 6: Open the PR**

Title: `feat: Grok Build as the fourth wi platform (#43)`. Body includes: the design-decision summary, the byte-stability checklist below, the rules inventory (files that reworded/moved rule text: none expected, all additive), and the spike/E2E evidence link.

PR checklist (mechanical):
```
- [ ] Claude/Codex/Copilot keep-alive & tool maps: additive only (byte-stable branches)
- [ ] validate.py: grok-tools + keep-alive/dev/research Grok markers; existing checks still hard-fail
- [ ] Manifest versions: three-way (or four-way if .grok-plugin) parity at 1.12.0
- [ ] Live: CLAUDE_PLUGIN_ROOT resolve + one ship/scan script succeeds under Grok (no pasted path)
- [ ] Live: scan + dev reach a PR under Grok /goal with one parallel spawn_subagent wave
```

---

## Self-review (author checklist, run after drafting)

- **Spec coverage:** every issue-#43 deliverable maps to a task - grok-tools.md (T2), keep-alive branch (T3), AGENTS.md row (T4), bootstrap (T4), models.md xAI + platform dim (T1), validate.py (T5), README (T6), manifests (T7). Live verification (T0, T8). No deliverable unmapped.
- **Placeholder scan:** the only deferred cells are `[from S-N]` (measured spike inputs, gathered in T0) and the conditional `.grok-plugin` (T7 Step 3 / T5 Step 4), which are genuine live-dependent decisions, not vague TODOs.
- **Byte-stability:** T3/T4/T6 each end with an additive-diff check; T8 Step 4 re-checks codex/copilot tool maps are byte-identical.
- **Type consistency:** `platform_model_for(agent, cfg, host)` and `XAI_BASE` are used consistently in T1 code and tests; `parse_models_config` returns the same key `platform_map` everywhere.
- **Scope:** MoA cross-vendor proposers (#34) are explicitly excluded; only routing-layer platform resolution is in scope.
