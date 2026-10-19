from pathlib import Path

import pytest
from st_package_reviewer.runner import CheckRunner

from lsp_review_checks.check_lsp_plugin import LspCheckLspPlugin


def run(path: Path, package_name: str) -> list[str]:
    runner = CheckRunner([LspCheckLspPlugin])
    runner.run(path, package_name=package_name)
    assert not runner.errors
    assert not runner.failures
    return [warning.message for warning in runner.warnings]


def make_package(path: Path, source: str, file_name: str = "plugin.py") -> None:
    (path / file_name).parent.mkdir(parents=True, exist_ok=True)
    (path / file_name).write_text(source, encoding="utf-8")


@pytest.mark.parametrize("source", [
    "from LSP.plugin import LspPlugin\n\nclass Foo(LspPlugin):\n    pass\n",
    "from lsp_utils import NodeManager\nfrom LSP.plugin import LspPlugin\n\nclass Foo(LspPlugin):\n    pass\n",
    # Not imported from LSP or lsp_utils.
    "class AbstractPlugin:\n    pass\n\nclass Foo(AbstractPlugin):\n    pass\n",
    "from LSP.plugin import AbstractPlugin\n\nisinstance(None, AbstractPlugin)\n",
])
def test_valid_plugin(tmp_path: Path, source: str) -> None:
    make_package(tmp_path, source)
    assert run(tmp_path, "LSP-foo") == []


@pytest.mark.parametrize("source, base", [
    ("from LSP.plugin import AbstractPlugin\n\nclass Foo(AbstractPlugin):\n    pass\n", "AbstractPlugin"),
    ("from LSP.plugin import (\n    AbstractPlugin as Base,\n    register_plugin,\n)\n\nclass Foo(Base):\n    pass\n",
     "AbstractPlugin"),
    ("from LSP.plugin.core.sessions import AbstractPlugin\n\nclass Foo(AbstractPlugin):\n    pass\n", "AbstractPlugin"),
    ("import LSP.plugin\n\nclass Foo(LSP.plugin.AbstractPlugin):\n    pass\n", "AbstractPlugin"),
    ("from lsp_utils import ClientHandler\n\nclass Foo(ClientHandler):\n    pass\n", "ClientHandler"),
    ("from lsp_utils import GenericClientHandler\n\nclass Foo(GenericClientHandler):\n    pass\n",
     "GenericClientHandler"),
    ("from lsp_utils import NpmClientHandler\n\nclass Foo(NpmClientHandler):\n    pass\n", "NpmClientHandler"),
    ("from lsp_utils.pip_client_handler import PipClientHandler\n\nclass Foo(PipClientHandler):\n    pass\n",
     "PipClientHandler"),
    ("import lsp_utils\n\nclass Foo(lsp_utils.NpmClientHandler):\n    pass\n", "NpmClientHandler"),
])
def test_deprecated_base(tmp_path: Path, source: str, base: str) -> None:
    make_package(tmp_path, source)
    [warning] = run(tmp_path, "LSP-foo")
    assert f"Class 'Foo' is based on the deprecated {base!r}" in warning
    assert "https://lsp.sublimetext.io/migrating_to_lsp_plugin/" in warning


@pytest.mark.parametrize("base, replacement", [
    ("AbstractPlugin", "'LspPlugin' instead"),
    ("NpmClientHandler", "'LspPlugin' with lsp_utils' 'NodeManager'"),
    ("PipClientHandler", "'LspPlugin' with lsp_utils' 'UvVenvManager'"),
])
def test_replacement_hint(tmp_path: Path, base: str, replacement: str) -> None:
    module = "LSP.plugin" if base == "AbstractPlugin" else "lsp_utils"
    make_package(tmp_path, f"from {module} import {base}\n\nclass Foo({base}):\n    pass\n")
    [warning] = run(tmp_path, "LSP-foo")
    assert f"Implement it using {replacement}" in warning


def test_plugin_in_subdirectory(tmp_path: Path) -> None:
    make_package(tmp_path, "from LSP.plugin import AbstractPlugin\n\nclass Foo(AbstractPlugin):\n    pass\n",
                 file_name="foo/plugin.py")
    [warning] = run(tmp_path, "LSP-foo")
    assert "Class 'Foo' is based on the deprecated 'AbstractPlugin'" in warning


def test_imports_do_not_leak_between_modules(tmp_path: Path) -> None:
    make_package(tmp_path, "from LSP.plugin import AbstractPlugin\n", file_name="a.py")
    make_package(tmp_path, "from .a import AbstractPlugin\n\nclass Foo(AbstractPlugin):\n    pass\n", file_name="b.py")
    assert run(tmp_path, "LSP-foo") == []


def test_non_lsp_package_is_skipped(tmp_path: Path) -> None:
    make_package(tmp_path, "from LSP.plugin import AbstractPlugin\n\nclass Foo(AbstractPlugin):\n    pass\n")
    assert run(tmp_path, "Foo") == []
