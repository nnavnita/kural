# Contributing to kural

Thanks for your interest in kural. This project is small and the rules are
short — please read them all before opening a PR.

## Workflow

1. **Fork** the repository and create a feature branch off `main`:
   ```bash
   git checkout -b feat/short-name
   ```
2. **Make your change** with tests and docs. New code must keep the project
   above the **80% line coverage** threshold (enforced in CI). Public
   functions and classes should carry a one-paragraph docstring.
3. **Run the local quality gates** before pushing:
   ```bash
   ruff check .
   ruff format --check .
   pytest          # runs the coverage gate too
   ```
4. **Open a pull request** against `main`. Direct pushes to `main` are
   blocked (see "Branch protection" below) — every change lands via a
   reviewed PR.
5. **Wait for CI**. The PR cannot be merged until the `Lint + tests +
   coverage` job is green on every supported Python version.

## What CI enforces

- `ruff check .` — lint passes
- `ruff format --check .` — code is formatted
- `pytest` — all tests pass on Python 3.10, 3.11, 3.12
- `--cov-fail-under=80` — line coverage stays at or above 80% (configured
  in `pyproject.toml` under `[tool.pytest.ini_options]`)

If you genuinely cannot test a piece of code (e.g. the asyncio entry
point in `kural/server.py:main`), mark it with `# pragma: no cover` and
say why in the PR description.

## Branch protection (repo admins)

To make the PR workflow non-bypassable, enable these rules on `main` in
GitHub → **Settings → Branches → Branch protection rules**:

- [x] Require a pull request before merging
- [x] Require approvals (1)
- [x] Dismiss stale pull request approvals when new commits are pushed
- [x] Require status checks to pass before merging
  - Required check: **`Lint + tests + coverage`** (every matrix entry)
- [x] Require branches to be up to date before merging
- [x] Require conversation resolution before merging
- [x] Do not allow bypassing the above settings
- [x] Restrict who can push to matching branches (admins only, used for
      emergency hotfixes)

Equivalent rules can also be expressed as a [GitHub repository ruleset]
if you prefer rulesets over classic branch protection.

[GitHub repository ruleset]: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets

## Reporting bugs / requesting features

Use [GitHub Issues](https://github.com/nnavnita/kural/issues). Include:

- What you were trying to do
- What happened instead (full traceback or log output, redacted of any
  secrets)
- Your OS, Python version, and `pip show pipecat-ai | grep Version`

## Code of conduct

Be kind. Disagree about the technical thing, not about the person.
