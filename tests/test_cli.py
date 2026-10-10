import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
PACKAGES = Path(__file__).parent / "packages"


def review(package, *args):
    return subprocess.run(
        [
            sys.executable, "-m", "st_package_reviewer",
            "--add-file-checkers", str(ROOT / "lsp_review_checks"),
            "--exclude", "CheckSettingsMenuEntry",
            "--package-name", package,
            *args,
            str(PACKAGES / package),
        ],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )


def test_valid_package_passes():
    result = review("LSP-valid", "--fail-on-warnings")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "No failures, no warnings." in result.stdout


@pytest.mark.parametrize("fail_on_warnings, returncode", [(False, 0), (True, 1)])
def test_missing_menu_is_reported(fail_on_warnings, returncode):
    result = review("LSP-missing-menu", *(["--fail-on-warnings"] if fail_on_warnings else []))
    assert result.returncode == returncode, result.stdout + result.stderr
    assert "missing 'Main.sublime-menu'" in result.stdout
    assert "'Main.sublime-menu' to add menu entries" not in result.stdout  # stock check excluded
