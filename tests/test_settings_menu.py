import json
from pathlib import Path
from typing import Any

import pytest
from st_package_reviewer.runner import CheckRunner

from lsp_review_checks.check_settings_menu import LspCheckSettingsMenu


def lsp_menu(caption: str, command: str = "edit_settings", base_file: str | None = None) -> list[dict[str, Any]]:
    entry: dict[str, Any] = {"caption": caption, "command": command}
    if base_file is not None:
        entry["args"] = {"base_file": base_file}
    return [{
        "id": "preferences",
        "children": [{
            "id": "package-settings",
            "children": [{
                "id": "lsp-settings",
                "children": [{"id": "lsp-servers", "children": [entry]}],
            }],
        }],
    }]


def run(path: Path, package_name: str) -> list[str]:
    runner = CheckRunner([LspCheckSettingsMenu])
    runner.run(path, package_name=package_name)
    assert not runner.errors
    assert not runner.failures
    return [warning.message for warning in runner.warnings]


def make_package(path: Path, name: str, menu: str | list[Any] | None = None) -> None:
    (path / f"{name}.sublime-settings").write_text("{}", encoding="utf-8")
    if menu is not None:
        text = menu if isinstance(menu, str) else json.dumps(menu)
        (path / "Main.sublime-menu").write_text(text, encoding="utf-8")


def test_valid_menu(tmp_path: Path) -> None:
    make_package(tmp_path, "LSP-foo", lsp_menu("LSP-foo", base_file="${packages}/LSP-foo/LSP-foo.sublime-settings"))
    assert run(tmp_path, "LSP-foo") == []


def test_valid_menu_with_comments_and_trailing_commas(tmp_path: Path) -> None:
    menu = json.dumps(lsp_menu("LSP-foo", base_file="${packages}/LSP-foo/LSP-foo.sublime-settings"), indent=2)
    make_package(tmp_path, "LSP-foo", "// comment\n" + menu.replace('"\n', '",\n'))
    assert run(tmp_path, "LSP-foo") == []


def test_no_settings_file(tmp_path: Path) -> None:
    assert run(tmp_path, "LSP-foo") == []


def test_missing_menu(tmp_path: Path) -> None:
    make_package(tmp_path, "LSP-foo")
    [warning] = run(tmp_path, "LSP-foo")
    assert "missing 'Main.sublime-menu'" in warning


@pytest.mark.parametrize("menu", [
    lsp_menu("LSP-bar", base_file="${packages}/LSP-foo/LSP-foo.sublime-settings"),
    [{"id": "preferences", "children": [{"id": "package-settings", "children": [{"caption": "LSP-foo"}]}]}],
    [],
])
def test_missing_entry(tmp_path: Path, menu: list[Any]) -> None:
    make_package(tmp_path, "LSP-foo", menu)
    [warning] = run(tmp_path, "LSP-foo")
    assert "has no entry for 'LSP-foo'" in warning


def test_wrong_command(tmp_path: Path) -> None:
    make_package(tmp_path, "LSP-foo", lsp_menu("LSP-foo", command="open_file"))
    [warning] = run(tmp_path, "LSP-foo")
    assert "'edit_settings' command" in warning


@pytest.mark.parametrize("base_file", [None, "${packages}/LSP-foo/Other.sublime-settings"])
def test_wrong_base_file(tmp_path: Path, base_file: str | None) -> None:
    make_package(tmp_path, "LSP-foo", lsp_menu("LSP-foo", base_file=base_file))
    [warning] = run(tmp_path, "LSP-foo")
    assert "'base_file' set to '${packages}/LSP-foo/LSP-foo.sublime-settings'" in warning


def test_invalid_json_is_left_to_stock_checks(tmp_path: Path) -> None:
    make_package(tmp_path, "LSP-foo", "[{")
    assert run(tmp_path, "LSP-foo") == []


def test_non_lsp_package_uses_stock_check(tmp_path: Path) -> None:
    make_package(tmp_path, "Foo", lsp_menu("Foo", base_file="${packages}/Foo/Foo.sublime-settings"))
    warnings = run(tmp_path, "Foo")
    assert warnings
    assert all("LSP > Servers" not in warning for warning in warnings)
