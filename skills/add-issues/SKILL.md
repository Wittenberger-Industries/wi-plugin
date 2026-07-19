---
type: Skill
name: add-issues
description: >
  File a well-formed GitHub issue - Bug, Feature, or Task - against the repo the session is
  connected to. Use whenever the user wants something tracked on GitHub: "file a bug",
  "open an issue", "create a GitHub issue for ...", "add a feature request", "track this as a
  task", "report this", or when they paste an error, stack trace, or failing output they want
  captured. Also use for filing follow-up issues discovered during other work. Not for editing,
  triaging, or closing existing issues. Gathers missing details, runs a bounded check/debug
  pass to fill gaps, confirms once, then publishes the issue via gh with type, labels, and
  relationships.
---

# /wit:add-issues - structured GitHub issue filing

One invocation → one published issue. Gather, investigate, confirm once, publish with `gh`.
The local draft is scaffolding for the confirm gate - it never outlives the run; GitHub is the
only source of truth. The quality bar: someone (human or agent) who has never seen this
conversation can pick the issue up and act on it.

**Infer before asking.** Classify and prefill everything possible from what the user already
gave (their words, pasted output, code in view). Collect what's genuinely missing in a single
batched question round - nobody wants a six-round interrogation to file a bug.

Design rationale for this skill lives in the wit repo's `docs/design-notes/add-issues.md`
(maintainer doc, never loaded at runtime) once written; the accepted design is
`docs/specs/2026-07-19-add-issue-skill-design.md`.

## Flow

### 1. Preflight

- `gh auth status` and `gh repo view --json nameWithOwner`. If either fails, stop and tell the
  user exactly what to fix.
- Note `gh --version` once per session: type / parent / dependency flags need ≥ 2.94.0
  (see `${CLAUDE_PLUGIN_ROOT}/skills/add-issues/references/gh-metadata.md`).
- Ensure `.wit/issues/` is self-gitignored before any draft lands (idempotent; same pattern as
  `.logs/` in workflow.md):
  `mkdir -p .wit/issues && printf '*\n' > .wit/issues/.gitignore`
  Do not rely on a root `.gitignore` entry - scan only seeds that on greenfield setup. The
  directory is transient staging and should be empty (see wit-directory.md). If a draft is
  sitting there, a previous run didn't finish - offer to resume it or discard it before
  starting fresh.

### 2. Classify and gather

- Infer the type from the seed: stack trace, "broken", regression → **Bug**; "add",
  "support", "allow", "it would be nice" → **Feature**; process, chore, refactor work →
  **Task**. Ask only when genuinely ambiguous.
- Read the matching template in
  `${CLAUDE_PLUGIN_ROOT}/skills/add-issues/references/templates.md` for that type's required
  sections.
- `gh label list --limit 100` → propose matching existing labels. Never invent label names;
  create one only if the user explicitly asks (`gh label create`).
- Milestone / assignee / parent / blocked-by: set only when the user mentions them or context
  implies them (e.g. "part of the MoA epic" → parent). Don't ask proactively.
- Ask ONE batched round for whatever required fields remain empty. Elicitation order: the
  superpowers plugin's brainstorming skill when available → wit's own brainstorm phase skill
  (`${CLAUDE_PLUGIN_ROOT}/skills/brainstorm/SKILL.md`) → plain batched questions only when
  neither exists. Then move on.

### 3. Investigate and dedup

- Run a bounded check/debug pass to fill what the user couldn't: verify the repro when it's
  cheap, read the failing test or stack frames to pin Root cause, capture Evidence, and name
  the concrete test for the acceptance criterion. Budget: ≤ 3 files, no tree scans - this is
  triage-level investigation, not the fix (`/wit:dev` owns that).
- `gh issue list --state open --search "<3-6 key terms>" --limit 10`. If a likely duplicate
  appears, show the top matches and ask: comment the fresh repro on the existing issue / link
  as related / create anyway / abort.

### 4. Draft, check, confirm

- Write `.wit/issues/<slug>.md` (kebab slug from the title; uniquify on collision) using the
  type's template and frontmatter from
  `${CLAUDE_PLUGIN_ROOT}/skills/add-issues/references/templates.md`.
- Run
  `python ${CLAUDE_PLUGIN_ROOT}/skills/add-issues/scripts/check_draft.py .wit/issues/<slug>.md`.
  It fails on missing sections or a Bug without a new-test acceptance criterion - fix the
  draft, don't argue with the checker. (python fallback: workflow.md "Script invocation".)
- Show the confirm gate: final title, a compact metadata table (type, labels, milestone,
  parent, blockers, assignees - plus anything that will be skipped and why), and the rendered
  body. Options: publish / edit / abort.
- `--auto` skips the gate but still runs the checker and lists every assumption made.

### 5. Publish and clean up

- Strip the draft's OKF frontmatter into a throwaway body file (dossier metadata, not issue
  text - same CRLF-safe awk as `${CLAUDE_PLUGIN_ROOT}/skills/ship/SKILL.md` ship:7; inlined so
  agents that only load add-issues never publish YAML), then create the issue:

  ```bash
  body=$(mktemp)
  awk '{sub(/\r$/,"")} NR==1&&$0=="---"{f=1;next} f&&$0=="---"{f=0;next} !f' .wit/issues/<slug>.md > "$body"
  gh issue create --title "…" --body-file "$body" [--type … --label … --milestone … --assignee …
    --parent … --blocked-by …]
  rm -f "$body"
  ```
- If a metadata flag fails: retry without it, log `skipped <capability> (<reason>)`, and try to
  set it post-create via `gh issue edit` where supported
  (`${CLAUDE_PLUGIN_ROOT}/skills/add-issues/references/gh-metadata.md` has the fallback map).
  An issue with a missing label beats no issue - never let optional metadata block creation.
- **On success: delete the draft.** `.wit/issues/` holds only unpublished work - the GitHub
  issue is now the single source of truth. On abort at the gate: delete it too. Only a failed
  `gh issue create` leaves the draft in place, so the next run can resume instead of
  re-interviewing.
- Report: issue URL, any skipped capabilities, and for Bug or Feature the handoff line:
  "Ready for `/wit:dev` with issue #<n> as the seed."

## Rules

- **Title:** `<area>: <symptom or outcome in user terms>` - ≤ 72 chars, no trailing period, no
  number prefix. Propose it; the user can override at the gate.
- **Bug acceptance criteria:** at least one criterion names a NEW automated test that fails on
  the bug and passes after the fix. This is the point of the skill - an issue without a test
  commitment invites a fix that quietly regresses. Override only with explicit user
  confirmation at the gate; make the relaxation visible in the issue itself (e.g. a manual
  repro checklist in the acceptance criteria) and rerun the checker with `--allow-no-test`.
- **Root cause:** never invent. Write `Unknown - needs investigation` when unknown; a wrong
  hypothesis stated confidently is worse than an honest gap.
- **Evidence:** when the seed contains command output or a stack trace, put the last ~30 lines
  in `## Evidence` verbatim and link anything longer. Repro fidelity is what makes bugs
  actionable.
- **Severity / priority:** existing labels only (`sev:high` etc.) - no extra frontmatter
  fields.
- **Repo issue templates:** `--body-file` bypasses `.github/ISSUE_TEMPLATE/`. If templates
  exist, mention that at the gate; use `--template` only on explicit request.
- **No AI attribution** in the issue title, body, or comments - same guardrail as ship.

## Bundled files

- `${CLAUDE_PLUGIN_ROOT}/skills/add-issues/references/templates.md` - per-type body templates +
  draft frontmatter. Read the one matching the classified type in step 2.
- `${CLAUDE_PLUGIN_ROOT}/skills/add-issues/references/gh-metadata.md` - flag matrix, version
  gates, post-create fallbacks, degradation contract. Read before using hierarchy/dependency
  flags or when a flag fails.
- `${CLAUDE_PLUGIN_ROOT}/skills/add-issues/scripts/check_draft.py` - deterministic draft
  validation. Always run before the confirm gate.
