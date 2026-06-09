# Cross-platform wi: Codex CLI + Copilot CLI support

- **Status:** Approved design — 2026-06-09
- **Branch:** `feat/cross-platform-copilot-codex`
- **Scope decision:** Copilot CLI + Codex CLI only (Gemini/Cursor/OpenCode explicitly out)
- **Structure decision:** flatten the repo to a single root-manifest plugin (the superpowers template)

---

## 1. Problem & goal

`wi` is a Claude Code plugin: a suite of `SKILL.md` skills plus two subagents that drive a low-token,
spec-driven, autonomous dev loop (`/wi:scan`, `/wi:dev`, `/wi:rpa`) to an open PR, kept alive by Claude
Code's built-in `/goal`. It currently assumes Claude Code throughout.

**Goal:** make the same plugin run on **OpenAI Codex CLI** and **GitHub Copilot CLI** with no fork —
one shared skill source, per-platform packaging, and per-platform adaptation only where a capability
genuinely differs. The model is exactly how `obra/superpowers` ships one source to many harnesses.

## 2. Scope

**In scope**
- Repo restructure to a flat root-manifest plugin.
- Codex CLI packaging + behavior parity (skills, `/goal`, subagents, worktrees).
- Copilot CLI packaging + behavior parity (skills, autopilot, `/fleet`, worktrees).
- Portability layer: `${CLAUDE_PLUGIN_ROOT}` handling, tool-name maps, a light bootstrap.
- Per-platform install docs + extended `validate.py`.

**Out of scope (non-goals)**
- Gemini CLI / Cursor / OpenCode / Factory Droid support (scoped out; the chosen pattern makes them
  cheap to add later).
- A monolithic Copilot "plugin installer" — Copilot has no plugin-bundle concept; skills are the unit.
- Rewriting wi's skill philosophy, the `.wi/` artifact model, or `rpa`'s UiPath specifics beyond the
  shared spine.
- Changing Claude Code runtime behavior (it must remain a no-op-equivalent for existing Claude users
  apart from the new install path).

## 3. Research findings — per-platform capability matrix

Confirmed from current (mid-2026) primary docs. Sources in §13.

| wi dependency | Claude Code | Codex CLI | Copilot CLI |
|---|---|---|---|
| `SKILL.md` skills (frontmatter + progressive load) | native | ✅ native Agent Skills | ✅ native Agent Skills (also reads `.claude/skills/`) |
| Plugin manifest | `.claude-plugin/plugin.json` (skills by convention) | `.codex-plugin/plugin.json` (`skills`/`hooks`/`mcpServers`/`apps` pointers) | none — skills are loose / `gh skill` |
| Marketplace | `.claude-plugin/marketplace.json` | reads `.agents/plugins/marketplace.json` **and `.claude-plugin/marketplace.json`** | `gh skill` registry / `github/awesome-copilot` |
| `/goal` keep-alive | built-in `/goal <cond>` | **native `/goal <cond>`** (persistent, default-on, hours/days) | no predicate `/goal`; **Autopilot**: `--autopilot --max-autopilot-continues N` (`--no-ask-user`, `--allow-all`/`--yolo`) |
| Subagents | `Agent`/`Task` | `spawn_agent` / `spawn_agents_on_csv` (parallel; `[agents] max_threads=6 max_depth=1`) | `task` tool + `/fleet` (`/tasks` to monitor) |
| Custom agent definition | `agents/*.md` | `.codex/agents/*.toml` / `~/.codex/agents/*.toml` (TOML) | `.github/agents/*.agent.md` |
| Git worktrees | native | native, **but sandbox may block branch/push (detached HEAD)** → commit-and-handoff | native |
| `${CLAUDE_PLUGIN_ROOT}` | native | **sets `CLAUDE_PLUGIN_ROOT` (compat) + `PLUGIN_ROOT`** for hooks; skill-script ctx to verify | none — reference bundled files by relative path from the skill dir |
| Custom slash commands | `/wi:*` native | `~/.codex/prompts/*.md` (**deprecated** → use skills, invoked `$name`) | none (open req #618/#1113) → skills invoked `/<skill-name>` |
| Built-in file/shell tools | Read/Write/Edit/Bash/Grep/Glob | `apply_patch`,`shell`,`web_search`,`view_image`,`update_plan` | `view`,`create`,`edit`,`apply_patch`,`bash`,`grep`,`glob`,`web_fetch` |
| MCP | yes | `[mcp_servers.*]` in `config.toml` / bundled `.mcp.json` | `~/.copilot/mcp-config.json` / project `.mcp.json` |
| superpowers / frontend-design soft-integration | Claude plugins | superpowers installable; detect generically | superpowers installable; detect generically |

**Headline:** both targets converged on the same open Agent Skills standard, so skill *bodies* are ~90%
portable. The work is packaging, path references, and parameterizing the autonomy spine — not rewriting
skills.

## 4. Target architecture — flattened root-manifest layout

```
wi-plugin/                     # repo root IS the plugin
├── .claude-plugin/
│   ├── marketplace.json       # plugins[0].source: "./"  (was "./plugins/wi"); Codex reads this too
│   └── plugin.json            # moved up from plugins/wi/.claude-plugin/plugin.json
├── .codex-plugin/
│   └── plugin.json            # NEW
├── skills/                    # moved up from plugins/wi/skills/  — CANONICAL, all 3 platforms
│   ├── scan/      {SKILL.md, references/, scripts/}
│   ├── dev/       {SKILL.md}
│   ├── research/  {SKILL.md, references/}
│   ├── plan/      {SKILL.md, references/}
│   ├── build/     {SKILL.md, references/}
│   ├── ship/      {SKILL.md, references/, scripts/}
│   ├── brainstorm/{SKILL.md, references/}
│   └── rpa/       {SKILL.md, references/}
├── agents/                    # moved up; task-runner.md + researcher.md (also used as prompt templates)
├── hooks/                     # CONDITIONAL (see §7.3/R5) — platform-aware session-start bootstrap,
│   ├── hooks.json             #   added only if AGENTS.md alone doesn't make skills auto-trigger
│   └── session-start
├── references/                # NEW — cross-platform tool maps
│   ├── copilot-tools.md
│   └── codex-tools.md
├── scripts/validate.py        # extended
├── docs/specs/                # design docs (this file)
├── AGENTS.md                  # NEW — bootstrap auto-read by Codex + Copilot
├── README.md                  # per-platform install
└── .gitignore                 # whitelist updated for the new top-level dirs
```

`plugins/` is removed. There is **one** canonical `skills/` dir; no duplication or symlinks (§5 covers how
each platform discovers it).

## 5. Per-platform packaging & install

### Claude Code (behavior unchanged; only the install path moves)
- `.claude-plugin/marketplace.json`: set `plugins[0].source` to `"./"`; keep name/description/version.
- `.claude-plugin/plugin.json`: move to repo root unchanged. Skills load from `./skills/` by convention.
- Install: `/plugin marketplace add Wittenberger-Industries/wi-plugin` → `/plugin install wi@wi`.

### Codex CLI
- Add `.codex-plugin/plugin.json`:
  ```json
  {
    "name": "wi",
    "version": "<match plugin.json>",
    "description": "<short>",
    "skills": "./skills/",
    "hooks": "./hooks/hooks.json"
  }
  ```
- Codex natively reads `.claude-plugin/marketplace.json`, so the existing marketplace manifest is the
  install entry point (its plugin flow / `/plugins`). Skills, native `/goal`, and `CLAUDE_PLUGIN_ROOT`
  compat work without further packaging.

### Copilot CLI
- No plugin bundle exists. The skill **is** the distributable unit.
- Install (documented in README): **clone the repo and `/skills add <cloned-repo>/skills`** to register the
  whole canonical dir at once — recommended, because wi skills are interdependent (cross-skill script refs +
  a plugin-version read need a shared root). Per-skill `gh skill install …` works for a one-off skill but
  breaks those cross-references, so it's discouraged for the full suite.
- `/wi:*` slash commands do not exist on Copilot → skills are invoked as `/<skill-name>` (e.g. `/dev`)
  or auto-trigger by `description`. Document the namespace difference; do not fight it.

## 6. The autonomy spine, made platform-aware

The only place skill *content* changes. Replace each hardcoded "Claude Code's built-in `/goal`" with a
platform-conditional block. Affected files: `skills/dev/SKILL.md`, `skills/research/SKILL.md`,
`skills/ship/SKILL.md`, `skills/build/references/worktrees-and-subagents.md`, and the two READMEs.

### 6.1 `/goal` keep-alive handoff
- **Claude** (today): `/goal The <slug> PR is open and its branch passes <cmds>; progress.md Phase is
  done. Constraints: …`
- **Codex**: native `/goal` — the *same* condition line, set via Codex's `/goal`. Near-identical.
- **Copilot**: no predicate `/goal`. Encode the completion condition in the run prompt and launch under
  Autopilot: `copilot --autopilot --max-autopilot-continues <N> --no-ask-user -p "<prompt incl.
  done-condition>"`. Document that completion is model-judged + continuation-capped, not a hard predicate.
- Keep wi's existing truth that it "works without `/goal`, just less robustly," so all three degrade to
  wi's own loop if the user doesn't arm persistence.

### 6.2 Subagent dispatch (build waves, researcher)
- The orchestrator's dispatch text becomes platform-aware via `references/{codex,copilot}-tools.md`:
  - Claude: `Agent`/`Task`.
  - Copilot: `task` tool / `/fleet` for parallel waves; `/tasks` to monitor.
  - Codex: `spawn_agent` (and `spawn_agents_on_csv`), bounded by `[agents] max_threads`. **Use generic
    fan-out with the task-runner/researcher prompt inlined** — repo-local named-agent dispatch is
    unreliable across Codex builds (open issues). The prompt skeleton already lives in
    `worktrees-and-subagents.md`, so this is a documentation/wiring change, not new behavior.
- `agents/*.md` stay as the canonical prompt templates + Claude agent definitions. Codex TOML mirrors are
  **optional** and skipped for now (the inline-prompt pattern makes them unnecessary).

### 6.3 Worktrees
- Add one fallback to `worktrees-and-subagents.md`: on Codex (or any sandbox) where branch/push is blocked
  / HEAD is detached, commit all work in place and hand off via the platform's native controls, emitting
  suggested branch name + commit message + PR body (mirrors superpowers' Codex finishing pattern). Detect
  with read-only `git rev-parse --git-dir/--git-common-dir` + `git branch --show-current`.

## 7. Portability layer

### 7.1 `${CLAUDE_PLUGIN_ROOT}` (209 references)
- **Keep them.** They resolve on Claude (native) and Codex (compat var).
- Add one rule to `copilot-tools.md` + `AGENTS.md`: *`${CLAUDE_PLUGIN_ROOT}` is the wi **plugin root** — the
  directory holding `skills/`, `agents/`, and `.claude-plugin/`.* On Claude/Codex it's the installed plugin
  dir (Codex sets the compat var); on Copilot it's the cloned wi repo (hence install wi **whole**, §5). The
  agent resolves every `${CLAUDE_PLUGIN_ROOT}/…` against that one root — this covers same-skill refs,
  **cross-skill refs** (`ship` → `skills/scan/scripts/check_mermaid.py`), and the plugin-root version read
  (`research` → `.claude-plugin/plugin.json`). The version read additionally needs a Copilot fallback
  ("if the file isn't present, omit the version") — see the plan.
- Rejected alternative: rewrite all 209 refs to skill-relative paths. Bigger diff, and bare relative
  paths are not guaranteed to resolve from the skill dir on Claude (CWD is the project). Revisit only if
  empirical testing shows Claude resolves skill-relative paths.

### 7.2 Tool-name maps
- Add `references/copilot-tools.md` and `references/codex-tools.md` (the superpowers tables, trimmed to
  what wi actually uses: subagent dispatch, file/shell verbs, the `${CLAUDE_PLUGIN_ROOT}` rule). wi's
  skills are mostly prose + raw `git`/shell, so the surface is small.

### 7.3 Bootstrap
- `AGENTS.md` at repo root (auto-read by Codex and Copilot) points the agent to "using wi" + the correct
  tool map so skills auto-trigger and tool names resolve off-Claude.
- `hooks/` carries a light, platform-aware `session-start` (superpowers-style env detection emitting the
  right JSON field per platform) **only if** needed to make skills auto-trigger; prefer the `AGENTS.md`
  route first to keep wi thin. Treat the hook as an enhancement, gated on testing.

## 8. Docs & validation
- README: three install sections (Claude / Codex / Copilot) + a short capability-differences note
  (`/goal` vs Autopilot, command namespace on Copilot).
- `scripts/validate.py`: validate `.codex-plugin/plugin.json` (JSON + required keys), the moved paths
  (skills/agents at root), presence of the tool-map files and `AGENTS.md`, and that the platform-aware
  handoff blocks exist in `dev`/`research`/`ship`.

## 9. Decisions (with rationale)
1. **Keep `${CLAUDE_PLUGIN_ROOT}` + a Copilot resolution rule** rather than rewriting 209 paths — lowest
   risk, smallest diff, preserves Claude + Codex behavior.
2. **One canonical `skills/` at root**; Copilot discovers it via `gh skill` / `/skills add` — no duplicate
   skill tree, no symlinks.
3. **Codex subagents = generic parallel fan-out with inlined prompts**; named-role TOMLs deferred.
4. **Light `AGENTS.md` bootstrap first**, full session-start hook only if auto-trigger needs it.
5. **Two platforms only** (Copilot + Codex); pattern keeps others cheap later.

## 10. Risks & things to verify empirically during build
- **R1** Does Claude's plugin loader still resolve skills at `./skills/` after the flatten with
  `source: "./"`? (High confidence — matches superpowers.) Verify by installing locally.
- **R2** Is `${CLAUDE_PLUGIN_ROOT}` set in Codex *skill* execution contexts (not just hook commands)?
  Docs confirm it for hooks; verify for skills. If not, the `copilot-tools.md`-style relative rule covers
  Codex too.
- **R3** Copilot skill discovery from a registered dir (`/skills add`) vs. `gh skill install` — confirm at
  least one path works end-to-end and document the recommended one.
- **R4** Codex `spawn_agent` parallelism honors `max_threads`; confirm the build-wave pattern doesn't
  exceed/deadlock and that the worktree-or-sandbox fallback triggers correctly.
- **R5** Auto-trigger off-Claude: confirm whether `AGENTS.md` alone makes skills fire, or the
  session-start hook is required (superpowers' acceptance test: a build-intent message triggers the
  brainstorm/dev skill).

## 11. Acceptance criteria
- [ ] Repo flattened: `skills/` and `agents/` at root, `plugins/` removed, `.claude-plugin/marketplace.json`
      `source: "./"`, `.gitignore` whitelist updated; `python scripts/validate.py` passes.
- [ ] `.codex-plugin/plugin.json` present and valid; a local Codex install surfaces the wi skills and
      `/goal` handoff works.
- [ ] Claude Code install still works from the flattened layout (skills load, `/wi:dev` runs).
- [ ] Copilot: at least one documented install path registers the skills; `/dev` (or auto-trigger) runs
      the loop; Autopilot handoff text is emitted instead of `/goal`.
- [ ] `dev`/`research`/`ship` emit platform-correct handoff text (Claude `/goal`, Codex `/goal`, Copilot
      Autopilot); `worktrees-and-subagents.md` documents the sandbox fallback.
- [ ] `references/copilot-tools.md` + `references/codex-tools.md` exist and include the
      `${CLAUDE_PLUGIN_ROOT}`→skill-dir rule; `AGENTS.md` bootstrap present.
- [ ] README has three install sections + the capability-differences note.
- [ ] No regression to `rpa` beyond the shared spine edits.

## 12. Rough work breakdown (feeds the plan)
1. **Flatten** the tree (git-move `plugins/wi/*` → root; update `.gitignore` whitelist + both manifests).
2. **Codex manifest** (`.codex-plugin/plugin.json`).
3. **Tool maps** (`references/copilot-tools.md`, `references/codex-tools.md`) incl. the path rule.
4. **Bootstrap** (`AGENTS.md`; `hooks/` only if §7.3/R5 require it).
5. **Spine parameterization** edits in `dev`/`research`/`ship`/`worktrees-and-subagents.md`.
6. **validate.py** extensions.
7. **README** per-platform install + differences note; plugin/marketplace descriptions updated.
8. **Verify** R1–R5 locally on each platform; capture results.

## 13. Sources
**Codex CLI:** developers.openai.com/codex — guides/agents-md, config-reference, skills, subagents,
plugins, plugins/build, hooks, mcp, cli/slash-commands, cli/reference, changelog; github.com/openai/codex
docs/config.md; Simon Willison "Codex subagents" (2026-03-16).
**Copilot CLI:** docs.github.com/en/copilot — copilot-cli customize (skills, agents, instructions, mcp),
reference/custom-agents-configuration, reference/copilot-cli-reference; github.blog changelog (custom
agents/delegate 2025-10-28, AGENTS.md 2025-08-28), fleet & autopilot concept pages; `gh skill` changelog
(2026-04-16); agentskills.io; github/awesome-copilot docs.
**Pattern reference:** `obra/superpowers` 5.1.0 — `.codex-plugin/plugin.json`, `.claude-plugin/` manifests,
`hooks/session-start`, `skills/using-superpowers/references/{copilot,codex}-tools.md`, README install
sections.
