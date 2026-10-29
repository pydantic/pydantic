You are backporting pull request #$PR_NUMBER of the Pydantic repository to the `$TARGET_BRANCH` maintenance branch.

The current directory is a checkout of `$TARGET_BRANCH`, with the merge commit of the PR (`$MERGE_SHA`, on `main`)
being cherry-picked. The cherry-pick stopped with conflicts. Your task is to resolve them so that the backport
applies the same change as the original PR, adapted to the state of `$TARGET_BRANCH`.

## Procedure

1. Understand the original change: `git show $MERGE_SHA`. Use `git log` and `git show` on `origin/main` to understand
   the context of conflicting hunks (e.g. which commits touched the conflicting lines on `main` but are not on
   `$TARGET_BRANCH`).
2. List the conflicts with `git status`, and resolve each conflicted file. Stage it with `git add` once resolved.
3. Run the tests related to the change (see "Running tests" below), and fix the backport if they fail.
4. Write the report (see "Report" below).

Do not commit, do not run `git cherry-pick --continue`/`--abort`, do not switch branches. Committing and opening
the PR is done after you exit.

## Rules

- The backport must only contain the change of the original PR. Do not refactor, do not fix unrelated issues,
  do not reformat code that wasn't touched by the PR.
- Never resolve a conflict by dropping the fix itself. If a test added by the PR can't be backported, adapt it
  to `$TARGET_BRANCH` rather than deleting it, and explain why in the report.
- If the change depends on other commits of `main` that are not on `$TARGET_BRANCH` (e.g. it uses a function
  introduced by an earlier PR), do not backport these other commits. Mark the backport as unresolved and list
  the missing PRs in the report: a maintainer will decide whether to backport them first.
- If you are not confident in a resolution, leave the conflict markers in place, mark the backport as unresolved
  and explain the remaining conflicts. A wrong resolution is worse than an unresolved one.

## Common conflicts

`main` is the development branch of the next major version (Pydantic V3), while `$TARGET_BRANCH` is a V2
maintenance branch. Code may have been moved, renamed or removed on `main`.

- `HISTORY.md`: never backport changelog changes, keep the `$TARGET_BRANCH` version of the file.
- Version numbers (`pydantic/version.py`, `pyproject.toml`, `pydantic-core/Cargo.toml`, ...): always keep the
  `$TARGET_BRANCH` versions.
- Lock files (`uv.lock`, `pydantic-core/Cargo.lock`): never edit by hand. Keep the `$TARGET_BRANCH` version, and if
  the PR changes dependencies, mention it in the report (dependency changes usually shouldn't be backported).
- CI and tooling configuration (`.github/`, `.pre-commit-config.yaml`, `Makefile`): keep the `$TARGET_BRANCH` version,
  unless the PR is specifically about CI or tooling.
- Deprecated APIs: V3 removes APIs that are deprecated in V2. If the fix touches code next to a deprecated code
  path that no longer exists on `main`, keep the deprecated code path on `$TARGET_BRANCH`, and apply the fix to it
  as well if relevant.
- Tests: the test suite may have been reorganized on `main`. Add the PR tests to the equivalent test module on
  `$TARGET_BRANCH`, and adapt them to V2 behavior and APIs.

<!-- Add more V3 specific conflicts below as they are encountered. -->

## Running tests

Pydantic and `pydantic-core` (in the `pydantic-core/` directory) are installed from source:

```bash
uv sync --frozen --all-groups --all-packages --all-extras
```

This builds `pydantic-core` (Rust), which takes a few minutes. Run it again if you change Rust code.

Then run the relevant test modules only (not the whole test suite), e.g.:

```bash
uv run pytest tests/test_main.py
uv run pytest pydantic-core/tests/validators/test_model.py
```

Also run `make lint` if you edited Python code.

## Report

Write a Markdown report to `$REPORT_FILE`. Its first line must be exactly `Status: resolved` or
`Status: unresolved`. Then, for each conflicted file, describe briefly how the conflict was resolved and why.
Include the tests you ran and their result. This report will be included in the backport PR description, to help
reviewers: be factual and concise.
