---
type: Plan
title: "Analysis: Grok Build as the fourth wi platform (issue #43)"
description: "Architecture review of issue #43's Grok Build adapter proposal against a live Grok Build 0.2.93 recon: confirms the thin-adapter shape and corrects three over-fits (predicate /goal vs model-judged, worktree conflation, stale model ids / Claude-centric routing). Feeds the #43 implementation plan and spec."
timestamp: 2026-07-12
tags: [analysis, grok, platform, portability]
---

# Analysis: Grok Build as 4th wi platform (Issue #43)

**Mode:** architecture review / red-flag notes (no implementation yet)  
**Sources:** [Issue #43](https://github.com/Wittenberger-Industries/wi-plugin/issues/43), wi-plugin `main` (adapter layer + 2026-06-09 cross-platform design), xAI docs + local Grok Build `0.2.93` (`~/.grok/docs`, `grok inspect`, `grok models`)

---

## Context

Issue #43 proposes adding **Grok Build** (`grok` CLI) as a fourth first-class platform beside Claude Code, Codex CLI, and Copilot CLI, using wi’s established **thin platform-adapter** pattern (tool map + keep-alive branch + AGENTS.md + bootstrap + models note). The direction is right; several runtime claims in the issue over-fit Grok to the Claude/Codex model and would produce a wrong keep-alive / worktree / models architecture if taken literally.

wi’s platform contract is already documented:

| Layer | What it is | Files today |
|-------|------------|-------------|
| Packaging | Root-manifest plugin | `.claude-plugin/*`, `.codex-plugin/plugin.json` |
| Tool / capability map | Claude names → platform names | `references/codex-tools.md`, `copilot-tools.md` |
| Keep-alive SSOT | Handoff templates only | `references/keep-alive.md` |
| Bootstrap | Off-Claude entry + path rule | `AGENTS.md`, `skills/scan/references/plugin-bootstrap.md` |
| Spine pointers | “print from keep-alive; dispatch via map” | `skills/dev`, `research`, `build/references/worktrees-and-subagents.md` |
| Validation | Portability files present | `scripts/validate.py` |

Grok is a **good** fourth target (Claude plugin/skills/agents compatibility is real; native parallel subagents + worktrees exist; superpowers is on xAI’s marketplace). It is **not** a drop-in of the Claude/Codex `/goal` semantics.

---

## What’s correct in the issue

1. **Scope boundary is right.** Touch the adapter layer only; leave platform-neutral phase skills (`.wi/` artifacts, DAG, gates) alone.
2. **Add-a-platform pattern is the right product shape.** New `references/grok-tools.md` + additive branches mirrors Codex/Copilot and matches `docs/specs/2026-06-09-cross-platform-copilot-codex-design.md` (“pattern keeps others cheap later”).
3. **Claude Code compatibility is real.** Docs + local `grok inspect` show Grok already loads Claude marketplace plugins (e.g. superpowers, uipath, vercel under `~/.claude/plugins/cache/`). Skills, agents, hooks, `AGENTS.md` / `CLAUDE.md` family are discovered with zero config. Superpowers as launch partner is accurate.
4. **Open questions that must be live-validated before merge** are the right gating style (install, namespace, keep-alive fidelity, model IDs).
5. **Optional `.grok-plugin/plugin.json` only if needed** matches how Codex got an explicit manifest while Claude’s layout remained primary.
6. **Byte-stability for existing platforms** is the correct safety claim.

---

## Red flags / issues (including mistakes in the issue itself)

### 1. Critical: Grok `/goal` ≠ Claude/Codex predicate `/goal`

The issue puts Grok on the **same `/goal` family branch** as Claude/Codex with the **same one-line predicate condition**, treating residual risk as “verification only.”

**Evidence of a real semantic gap:**

| | Claude Code / Codex `/goal` | Grok Build `/goal` |
|--|-----------------------------|--------------------|
| UX | `/goal <condition>` | `/goal <objective>` (+ `status\|pause\|resume\|clear`) |
| Completion | Platform (re)evaluates a **predicate** until true | Agent drives via **`update_goal`**; marks `completed: true` when **it** judges work done/verified |
| Docs language | Condition / keep-alive predicate | “Works toward the objective… completed and verified” (self-planned checklist) |
| Local doc | — | “Availability: only when goal feature enabled **and `update_goal` tool is in the session toolset**” |

So Grok’s keep-alive is closer to **Copilot Autopilot (model-judged + tool/loop-bounded)** with nicer pause/resume UX than to Claude’s hard predicate. Putting Grok “on the Claude/Codex branch” without a **model-judged caveat + unattended warning** under-documents the real failure mode: the agent can self-complete without PR remote checks green / `progress.md Phase = done`.

The issue even **contradicts itself**: Summary says persistence is “closed by `/goal`,” while “Why this approach is safe” still says the soft spot is “keep-alive without a predicate goal.” That leftover is a signal the filing jumped categories after the 2026-06-22 announcement without re-architecting the keep-alive branch.

**Correct framing:** same *template text* as the condition line is still useful (tells the agent *what* “done” means), but the branch must be labeled **objective + model-judged verification**, not **predicate `/goal`**.

### 2. Critical: worktree conflation (three different mechanisms)

The issue equates Grok’s “native worktrees” with “the exact primitives wi’s build phase relies on.” Those are **three layers**:

| Mechanism | Owner | Purpose |
|-----------|--------|---------|
| Session `-w / --worktree` | Grok CLI | Isolate **whole session** under `~/.grok/worktrees/...` |
| Feature worktree `git worktree add -b wi/<slug> ...` | wi build | Feature branch isolation; orchestrator commits here |
| Subagent `isolation: worktree` | Grok `spawn_subagent` | Per-child isolated tree + merge-back |

wi’s default is: **one feature worktree, many parallel runners with disjoint files, orchestrator sole committer** (`worktrees-and-subagents.md`). Mapping every runner to `isolation: worktree` would change merge semantics and cost (env install per tree). Starting `grok -w` *and* creating `../repo-wi-slug` risks **nested/detached worktrees** and ship cleanup confusion.

**Correct framing:** document session worktree as optional outer shell; wi-managed feature worktree remains canonical; use Grok subagent worktree isolation only as wi’s **level-2 escalate** (file collision / non-parallel-safe tests), analogous to Codex’s shared-tree default.

### 3. High: model ID and routing assumptions are stale / Claude-centric

- Issue examples (`grok-code-fast`, `grok-4`) do **not** match local `grok models` on this machine: **`grok-4.5`** (default), **`grok-composer-2.5-fast`**. Always resolve via `grok models` at doc-write time.
- Entire `references/models.md` is Claude dispatch tokens (`fable|opus|sonnet|haiku`). Under Grok, **all** dispatches are Grok models; “subagents can only run Claude models” is Claude-Agent-tool-specific — issue notes a caveat, but the **config surface** (presets, floors, MoA proposers) needs a **platform column or Grok preset mapping**, not one sentence.
- Issue §6a: “add xAI as cross-provider for family diversity” is **right when running on Claude/Codex/Copilot**, and **wrong as the diversity story when the host is already Grok** (Grok reviewing Grok is same-family). On Grok host, cross-provider defaults should prefer **OpenAI or Anthropic**, not xAI.

### 4. High: `${CLAUDE_PLUGIN_ROOT}` is not free in all contexts

Grok docs set **`GROK_PLUGIN_ROOT` / `GROK_PLUGIN_DATA`**, with **`CLAUDE_PLUGIN_ROOT` / `CLAUDE_PLUGIN_DATA` aliases for hooks**. Session env in this interactive run had those vars **empty**. Codex’s “compat var just works” claim is stronger than Grok’s proven surface.

**Correct rule (same as Copilot’s):** `${CLAUDE_PLUGIN_ROOT}` means the **wi plugin root** (dir holding `skills/`, `agents/`, `.claude-plugin/`) — installed plugin path or clone — whether or not the env var is set. State this explicitly in `grok-tools.md`.

### 5. Medium: packaging / enablement gaps the issue understates

- Manifest optional is true; install still needs **`grok plugin install … --trust`** (hooks/MCP stay inactive until trusted).
- Config model: plugins can be **disabled until explicitly enabled** (`[plugins] enabled` / modal). Document enable after install.
- Marketplace path for *publishing* wi is a PR to `xai-org/plugin-marketplace`, not only user `[[marketplace.sources]]`. Distinguish **user install** vs **official catalog listing**.
- `validate.py` today requires `references/{codex,copilot}-tools.md` and Copilot Autopilot branches in dev/research. Issue implementation list **omits** extending validation (and version/description strings that still say “three platforms”).

### 6. Medium: namespace / skill invocation

- Skill frontmatter names are `scan` / `dev` / `rpa` (not `wi:dev`). On Grok, user-invocable skills become **`/<skill-name>`**, with collisions resolved as **`/<scope-or-plugin>:<name>`**.
- Claude’s `/wi:scan` is **not** guaranteed; expect `/scan`, `/dev`, `/wi:scan` (qualified), or natural-language auto-trigger. Flat aliases (`wi-scan`, …) remain valuable for one-token UX and cross-harness muscle memory — not “maybe.”
- Built-in **`/plan`** exists on Grok; wi’s `plan` skill is `user-invocable: false`, so picker collision is fine, but docs should not tell users to run `/plan` for wi.

### 7. Medium: subagent dispatch API mismatch

wi skills say “Agent/Task / spawn_agent / task+fleet.” Grok’s tool is **`spawn_subagent`** with built-ins `general-purpose | explore | plan`, **depth limit 1**, optional `capability_mode`, `isolation`, `background`.

**Correct map (Codex-style, not Claude named-role):

| wi role | Grok dispatch |
|---------|----------------|
| `wi-task-runner` | `general-purpose`, prompt = inlined `agents/wi-task-runner.md` contract + task skeleton; **shared** feature worktree (`isolation: none`) |
| `wi-researcher` | `explore` (read-only-ish) **or** `general-purpose` + read-only capability; inline researcher contract |
| `wi-code-checker` | `general-purpose` (or plan only if truly non-editing); inline checker contract; never assume Claude registered agent name works |

Named `agents/*.md` may load as Grok agent definitions via Claude compat — **verify**, but do not depend on named-role dispatch (Codex lesson).

### 8. Medium: headless fallback details

- `-p / --single` is documented as a **single user prompt** that can still run a multi-tool agent loop; pair with `--max-turns`, `--always-approve` / `--yolo`, session `--continue` / `--resume`.
- Grok also has **`--check`** (self-verification loop, headless only) — issue never mentions it; may complement or confuse wi’s own verification gate. Treat as optional footnote after live test, not primary keep-alive.
- Unattended warning (same spirit as Copilot’s ⚠️) is mandatory if documenting `--always-approve`.

### 9. Lower but real

- **Tokens / ledger:** Copilot got a full “credits / unavailable per-task” section. Grok has `/usage`. Issue ignores ledger portability; `token_report.py` Claude transcript paths will not work. Mirror Copilot: duration from wi stamps; usage only when user/session exposes figures.
- **Success criteria include `/wi:rpa` end-to-end.** RPA depends on UiPath skill ecosystem (already Claude-cache-discoverable here) + tenant auth. Treat as **stretch**, not merge gate; gate on `scan` + `dev` to open PR.
- **Effort “Low–Medium” is optimistic** if keep-alive is reclassified and models presets need Grok IDs. Closer to **Medium**, same as original Codex/Copilot spine work, with beta live-run dependency.
- **Design-scope history:** 2026-06-09 explicitly scoped Gemini/Cursor/OpenCode out; Grok is new scope but fits the extension pattern — still deserves a short design note (or issue amendment), not only a laundry list of file edits.
- **“Near drop-in” oversells runtime.** Packaging is near drop-in; **execution still requires the tool map** (Claude tool names in skill prose → Grok tools). Same as every other non-Claude host.

---

## Correct architecture (recommended)

### Principle

> **Same source skills; Grok is a fourth harness adapter.**  
> Packaging rides Claude-compatible discovery.  
> Autonomy spine (keep-alive, subagent dispatch, worktrees, model tokens, usage) is **platform-conditional**, with Grok treated as **Claude-compatible packaging + Copilot-class completion semantics + first-class subagent/worktree CLI**.

### Component design

```
                    ┌─────────────────────────────────────┐
                    │  Platform-neutral wi core           │
                    │  skills/*  agents/*  .wi/ artifacts │
                    └─────────────────┬───────────────────┘
                                      │ reads maps / keep-alive SSOT
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
   Claude Code                  Codex / Copilot              Grok Build
   native Agent + /goal         existing maps                grok-tools.md
   predicate keep-alive         keep-alive branches          keep-alive: Grok branch
                                                             (objective /goal +
                                                              model-judged done)
```

### 1. Packaging & install

- **Primary:** `grok plugin install Wittenberger-Industries/wi-plugin --trust` (or marketplace once listed), then **enable** if disabled-by-default.
- **Compat fallback:** clone + `--plugin-dir` / `[plugins] paths` / Claude-cache discovery if user already uses Claude plugins.
- **Defer** `.grok-plugin/plugin.json` until a real install fails without it.
- Document **official catalog** as separate (PR to `xai-org/plugin-marketplace`).
- Bootstrap (`plugin-bootstrap.md`): superpowers via Grok marketplace / Claude compat; flat `wi-*` aliases into `~/.agents/skills/` and/or `~/.grok/skills/` as live-tested.

### 2. `references/grok-tools.md` (capability map)

Must include:

- **Plugin root rule** (`${CLAUDE_PLUGIN_ROOT}` = wi root; `GROK_PLUGIN_ROOT` alias on hooks only).
- **Tool table** (Claude → Grok): file/shell/search/web; `TodoWrite` → `todo_write`; subagent → `spawn_subagent`; etc.
- **Dispatch recipe** (inline prompts, Codex-style; table above).
- **Worktree policy** (feature tree canonical; no double-nest; subagent isolation = escalate only).
- **Keep-alive pointer** to Grok branch in `keep-alive.md`.
- **Models:** `grok models` IDs; how to pass model on spawn/session; orchestrator informational.
- **Usage/ledger** notes (Copilot-analogue honesty).
- **Permissions:** `--always-approve` / permission modes / sandbox flags for unattended.

### 3. Keep-alive (the main design correction)

**Three branches, not two:**

1. **Claude Code / Codex** — predicate `/goal` + one-line condition (unchanged).
2. **Copilot** — Autopilot relaunch + ⚠️ (unchanged).
3. **Grok Build (new)** — arm:
   ```
   /goal The <slug> PR is open with its remote checks green (or none configured) and its branch passes <lint+test>; .wi/features/<slug>/progress.md Phase is done. Constraints: only files named in tasks.md change; never force-push; tests are never weakened to pass.
   ```
   **Plus explicit notes:**
   - Completion is **agent-judged** via goal/verification loop (`update_goal`); treat condition text as the **definition of done**, not a platform predicate.
   - Prefer `/goal pause|resume` for auth-gate stops.
   - Single-line paste still recommended (harmless; matches other platforms).
   - ⚠️ Unattended / `--always-approve` warning (same class as Copilot).
   - Headless fallback: `grok -p "<prompt incl. done-condition>" --always-approve --max-turns <N>` with `--continue` / session resume; verify multi-step behavior live before documenting as CI path.
   - Do **not** claim parity with Claude’s remote-check predicate until a live run proves the agent actually checks PR status + local gate before `completed: true`.

Optional later hardening (out of scope for first PR unless easy): a tiny ship-side “goal still armed?” note in progress.md when Grok self-completes early.

### 4. Spine pointers (additive only)

| File | Change |
|------|--------|
| `AGENTS.md` | Grok row → `references/grok-tools.md`; invoke + persistence lines name Grok |
| `skills/dev/SKILL.md` §4, `skills/research/SKILL.md` | Platform-aware handoff includes Grok branch from keep-alive SSOT |
| `skills/build/references/worktrees-and-subagents.md` | Add Grok to dispatch mechanism list + worktree policy |
| `skills/scan/references/plugin-bootstrap.md` | Install + aliases + superpowers on Grok |
| `references/skill-aliases/*` | Descriptions mention Grok slash form if needed |
| `references/models.md` | Host-Grok model ID mapping; cross-provider: xAI for *other* hosts; OpenAI/Anthropic when host is Grok |
| `README.md` | Fourth column in matrix + install |
| `scripts/validate.py` | Require `grok-tools.md`; require Grok branch strings in keep-alive + dev/research; update platform descriptions |
| Manifests / descriptions | Bump version when shipping; mention Grok in plugin description keywords |

**Do not** rewrite phase skill algorithms for Grok.

### 5. What “done” means for the first merge

Minimum bar (tighter than issue success criteria):

1. Documented install path works on a real Grok session (`grok plugin install` or verified Claude-compat load).
2. Entry skills invocable (documented exact slash form after live check).
3. `dev` handoff prints Grok keep-alive branch; a short run exercises `/goal` + at least one parallel `spawn_subagent` wave in a feature worktree.
4. `validate.py` green; Claude/Codex/Copilot branches byte-stable.
5. Open questions checklist filled with **measured** answers (even if “predicate not enforced; model-judged”).

Stretch: full hands-off PR; rpa; marketplace listing; `.grok-plugin` only if required.

---

## Suggested sequencing (if implementing later)

1. **Spike (half day, real Grok session):** install wi, note slash names, env vars, `/goal` + `update_goal` behavior against a fake condition, subagent named vs inline, worktree nesting. Capture answers in the issue.
2. **Adapter PR:** `grok-tools.md` + keep-alive Grok branch + AGENTS + validate + README (docs-first, correct semantics).
3. **Spine pointers:** dev/research/build/bootstrap/models.
4. **Live E2E:** `scan` + small `dev` to PR under `/goal`.
5. **Only then** claim “fourth platform” in marketing copy; keep “model-judged keep-alive” honest.

---

## Verification (for a future implementation)

- Static: `python scripts/validate.py`
- Live Grok:
  - `grok plugin install <path|repo> --trust` → `grok inspect --json` shows wi skills/agents
  - Invoke entry skill by documented slash form
  - Arm Grok keep-alive line; confirm pause/resume; deliberately fail a condition clause and see whether agent still completes
  - Parallel task-runner wave without nested session worktrees
  - Confirm no regression instructions for Claude/Codex/Copilot in the same files (diff review)

---

## Bottom line

| Issue claim | Verdict |
|-------------|---------|
| Thin adapter, additive only | **Correct** |
| Near drop-in packaging via Claude compat | **Mostly correct** (trust/enable + namespace still TBD live) |
| Join Claude/Codex predicate `/goal` branch | **Incorrect / incomplete** — use **third branch**: objective `/goal` + model-judged done + Copilot-class warning |
| Worktrees “map directly” to wi build | **Overstated** — three mechanisms; define policy |
| Persistence problem “closed” | **Overstated** — UX closed; **predicate fidelity open** |
| models.md + xAI cross-provider | **Partial** — map Grok IDs; xAI cross-provider for *other* hosts; not diversity on Grok host |
| Effort low–medium, risk low–medium | **Effort medium**; risk medium until live `/goal` fidelity known |
| validate.py / ledger / worktrees-and-subagents | **Under-specified** in issue — must be in scope |

**Correct architecture:** extend the 2026-06-09 portability layer with `grok-tools.md` and a **dedicated Grok keep-alive branch** that reuses the condition *text* but documents **agent-judged completion**, Codex-style **inline subagent dispatch**, and a **clear worktree layering policy** — not a fourth copy of Claude’s predicate semantics.
