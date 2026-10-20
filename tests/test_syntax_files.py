from pathlib import Path

import pytest
from st_package_reviewer.runner import CheckRunner

from lsp_review_checks.check_syntax_files import LspCheckSyntaxFiles

HEADER = "%YAML 1.2\n---\nname: Foo\nscope: source.foo\n"
CONTEXTS = "contexts:\n  main:\n    - match: foo\n      scope: keyword.foo\n"


def run(path: Path, package_name: str = "LSP-foo") -> list[str]:
    runner = CheckRunner([LspCheckSyntaxFiles])
    runner.run(path, package_name=package_name)
    assert not runner.errors
    assert not runner.failures
    return [warning.message for warning in runner.warnings]


def make_syntax(path: Path, text: str, file_name: str = "Foo.sublime-syntax") -> None:
    (path / file_name).parent.mkdir(parents=True, exist_ok=True)
    (path / file_name).write_text(text, encoding="utf-8")


def test_no_syntax_files(tmp_path: Path) -> None:
    assert run(tmp_path) == []


@pytest.mark.parametrize("hidden", ["hidden: true", "hidden:true", "hidden: True  # internal", "hidden: TRUE"])
def test_hidden_syntax(tmp_path: Path, hidden: str) -> None:
    make_syntax(tmp_path, f"{HEADER}{hidden}\n{CONTEXTS}")
    assert run(tmp_path) == []


@pytest.mark.parametrize("text", [
    f"{HEADER}{CONTEXTS}",
    f"{HEADER}hidden: false\n{CONTEXTS}",
    # Not a top-level key.
    f"{HEADER}variables:\n  hidden: true\n{CONTEXTS}",
    f"{HEADER}contexts:\n  main:\n    - match: |\n        hidden: true\n      scope: keyword.foo\n",
    f"{HEADER}# hidden: true\n{CONTEXTS}",
])
def test_visible_syntax(tmp_path: Path, text: str) -> None:
    make_syntax(tmp_path, text)
    [warning] = run(tmp_path)
    assert "provides a syntax that is not hidden" in warning
    assert "dedicated package" in warning
    assert "https://github.com/sublimehq/package_control_channel" in warning


def test_reports_each_visible_syntax(tmp_path: Path) -> None:
    make_syntax(tmp_path, f"{HEADER}{CONTEXTS}", file_name="syntaxes/Foo.sublime-syntax")
    make_syntax(tmp_path, f"{HEADER}{CONTEXTS}", file_name="syntaxes/Bar.sublime-syntax")
    make_syntax(tmp_path, f"{HEADER}hidden: true\n{CONTEXTS}", file_name="syntaxes/Panel.sublime-syntax")
    assert len(run(tmp_path)) == 2
