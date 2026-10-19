import json
from pathlib import Path
from typing import Any

import pytest
from st_package_reviewer.runner import CheckRunner

from lsp_review_checks.check_settings_file import LspCheckSettingsFile


def run(path: Path, package_name: str) -> list[str]:
    runner = CheckRunner([LspCheckSettingsFile])
    runner.run(path, package_name=package_name)
    assert not runner.errors
    assert not runner.failures
    return [warning.message for warning in runner.warnings]


def make_package(path: Path, name: str, settings: str | dict[str, Any]) -> None:
    text = settings if isinstance(settings, str) else json.dumps(settings)
    (path / f"{name}.sublime-settings").write_text(text, encoding="utf-8")


@pytest.mark.parametrize("settings", [
    {},
    {"enabled": False},
    {"initialization_options": {"foo": 1}, "settings": {"foo.bar": True}},
    "// comment\n{\"enabled\": false,}",
])
def test_valid_settings(tmp_path: Path, settings: str | dict[str, Any]) -> None:
    make_package(tmp_path, "LSP-foo", settings)
    assert run(tmp_path, "LSP-foo") == []


def test_no_settings_file(tmp_path: Path) -> None:
    assert run(tmp_path, "LSP-foo") == []


@pytest.mark.parametrize("enabled", [True, None, "false"])
def test_enabled_not_false(tmp_path: Path, enabled: Any) -> None:
    make_package(tmp_path, "LSP-foo", {"enabled": enabled})
    [warning] = run(tmp_path, "LSP-foo")
    assert "should not specify 'enabled' unless it is set to false" in warning


@pytest.mark.parametrize("key", ["initialization_options", "settings"])
@pytest.mark.parametrize("value", [{}, None, []])
def test_empty_object(tmp_path: Path, key: str, value: Any) -> None:
    make_package(tmp_path, "LSP-foo", {key: value})
    [warning] = run(tmp_path, "LSP-foo")
    assert f"should not specify {key!r} unless it includes any keys" in warning


@pytest.mark.parametrize("key, replacement", [
    ("initializationOptions", "'initialization_options'"),
    ("ignore_server_trigger_chars", "'disabled_capabilities'"),
])
def test_deprecated_key(tmp_path: Path, key: str, replacement: str) -> None:
    make_package(tmp_path, "LSP-foo", {key: {"foo": 1} if key == "initializationOptions" else True})
    [warning] = run(tmp_path, "LSP-foo")
    assert f"uses the deprecated {key!r} setting" in warning
    assert replacement in warning


@pytest.mark.parametrize("settings", ["{", "[]"])
def test_invalid_settings_are_left_to_stock_checks(tmp_path: Path, settings: str) -> None:
    make_package(tmp_path, "LSP-foo", settings)
    assert run(tmp_path, "LSP-foo") == []


def test_non_lsp_package_is_skipped(tmp_path: Path) -> None:
    make_package(tmp_path, "Foo", {"enabled": True, "settings": {}})
    assert run(tmp_path, "Foo") == []
