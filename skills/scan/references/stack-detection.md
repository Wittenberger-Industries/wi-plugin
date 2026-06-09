# Stack detection cookbook

Detect by reading config files and lockfiles, not source. Below: what to look for, and what command to
record in `repo-map.md` when you find it. Python is first-class; other stacks are detected generically.

## Signal files (one pass)

Run something like `git ls-files | head -200` plus a look at the root. Map these signals:

| File / dir | Means | Record |
|------------|-------|--------|
| `pyproject.toml` | Python project | read `[project]`, `[tool.*]` for deps, ruff, mypy, pytest |
| `uv.lock` | uv-managed | install `uv sync`; run `uv run <cmd>` |
| `poetry.lock` | Poetry | install `poetry install`; run `poetry run <cmd>` |
| `requirements*.txt` | pip | install `pip install -r requirements.txt` |
| `setup.cfg` / `tox.ini` | older Python config | check for pytest/flake8 settings |
| `package.json` | Node/JS/TS | read `scripts`, `devDependencies` |
| `pnpm-lock.yaml` / `yarn.lock` / `package-lock.json` | pnpm / yarn / npm | pick the matching runner |
| `tsconfig.json` | TypeScript | typecheck `tsc --noEmit` (or the project's script) |
| `go.mod` | Go | test `go test ./...`; build `go build ./...` |
| `Cargo.toml` | Rust | test `cargo test`; lint `cargo clippy`; fmt `cargo fmt` |
| `Makefile` / `Justfile` / `Taskfile.yml` | task runner | the `test`/`lint`/`build` targets are authoritative |
| `.github/workflows/*` | GitHub Actions CI | the steps reveal the *real* canonical commands |
| `.pre-commit-config.yaml` | pre-commit hooks | the hooks are the enforced lint/format set |
| `Dockerfile` / `compose.yml` | containerized run | note how the app is started |

**The Makefile / CI steps win.** If `pyproject.toml` says ruff but CI runs `make lint`, record `make lint`
— that's what actually gates merges.

## Python specifics

- **Test:** `pytest` (all) and `pytest <file>::<TestClass>::<test_name>` (one). With uv: `uv run pytest`.
- **Lint/format:** `ruff check .` / `ruff format .` (modern); else flake8/black/isort as configured.
- **Types:** `mypy <pkg>` or `pyright`, if configured in `pyproject.toml`.
- **Layout:** `src/<pkg>/` (src layout) vs flat `<pkg>/`. Note which — it affects imports and test paths.
- **Env:** virtualenv? uv-managed? Record how to get a working interpreter.

## JS / TS specifics

- The `scripts` block in `package.json` is the source of truth: `test`, `lint`, `typecheck`, `build`,
  `dev`. Record them verbatim with the detected runner (`pnpm test`, `npm run test`, ...).
- Test runner is usually vitest or jest — note how to run a single test file.
- Frontend framework (React/Next/Vue/Svelte) → flag for design-skill routing.

## Other stacks

Go, Rust, Java/Gradle, Ruby, etc.: find the build tool's config, record its standard test/lint/build
commands, and note anything non-standard. When genuinely unsure, write `UNKNOWN — ask` rather than guess.

## Verify before you record

Cheap sanity checks make the map trustworthy:

- Run the **test** command in a dry/`--collect-only` mode if available (e.g. `pytest --collect-only`) to
  confirm it's wired up.
- Confirm the lint and typecheck binaries resolve.
- If a command errors because of a missing install step, record the install step too.

A `repo-map.md` whose commands actually run is the difference between a smooth build phase and one that
stalls on a wrong command.

## Parallel-safety of tests

build executes tasks in concurrent waves, so record whether the suite tolerates parallel runs:

- `pytest-xdist` (`-n`) configured, tests using `tmp_path`/isolated fixtures -> likely **yes**.
- A shared on-disk DB (single sqlite file), fixed ports, global state files, order-dependent tests ->
  **no**.
- Can't tell cheaply -> **unknown** (build will then run Verify commands serially after each wave instead
  of guessing).

Record the answer as `Tests parallel-safe:` in `repo-map.md`'s Commands block.
