# lsp-package-reviewer-checks

Additional [st_package_reviewer](https://github.com/kaste/st_package_reviewer) checks for packages registered in
[sublimelsp/repository](https://github.com/sublimelsp/repository). The reviewer loads them through its
`--add-file-checkers` option and runs them alongside its built-in checks. See the reviewer's
[addon docs](https://github.com/kaste/st_package_reviewer/blob/main/docs/addons.md) for the checker API.

## Checks

- `LspCheckSettingsMenu` (replaces `CheckSettingsMenuEntry`) - `LSP-*` packages must have a
  `Preferences > Package Settings > LSP > Servers > <package>` menu entry that opens `<package>.sublime-settings`
  with `edit_settings`. Other packages fall back to the stock check.

Checks that replace a stock check require that check to be disabled with `--exclude` (or the `exclude` action input).

## Layout

- `lsp_review_checks/` - the checkers. This directory (and only this one) is passed to `--add-file-checkers`, and
  every module in it is imported, so don't put tests or fixtures here. Class names are prefixed with `Lsp`.
- `tests/` - unit tests (using `CheckRunner` directly) and CLI smoke tests against packages in `tests/packages/`.

## Development

Requires [uv](https://docs.astral.sh/uv/). The reviewer is installed as a dependency, pinned in `pyproject.toml`.

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
```

Review a local package checkout:

```bash
uv run st_package_reviewer --add-file-checkers lsp_review_checks --exclude CheckSettingsMenuEntry \
  --package-name LSP-foo /path/to/LSP-foo
```

Review a real pull request in sublimelsp/repository (requires a reviewer checkout, here in `../st_package_reviewer`, and
a GitHub token for crawling the packages, here taken from the [GitHub CLI](https://cli.github.com/)):

```bash
GITHUB_TOKEN=$(gh auth token) uv run python -u ../st_package_reviewer/gh_action/action.py \
  --pr https://github.com/sublimelsp/repository/pull/123 \
  --add-file-checkers lsp_review_checks --exclude CheckSettingsMenuEntry
```

The result is written to `review.md`.

## Usage in GitHub Actions

```yaml
- uses: actions/checkout@<sha>
  with:
    repository: sublimelsp/lsp-package-reviewer-checks
    ref: <trusted commit sha>
    path: lsp-package-reviewer-checks

- uses: kaste/st_package_reviewer/gh_action@<sha>
  with:
    pr: ${{ github.event.pull_request.html_url }}
    add-file-checkers: lsp-package-reviewer-checks/lsp_review_checks
    exclude: CheckSettingsMenuEntry
```

The checks are executed as Python code with the reviewer's privileges, so pin them to a reviewed commit. When bumping
the reviewer version used in the workflow, bump the `st-package-reviewer` revision in `pyproject.toml` as well
(`uv lock --upgrade-package st-package-reviewer`).
