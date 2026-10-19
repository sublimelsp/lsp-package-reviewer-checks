import ast

from st_package_reviewer.check.file.ast import AstChecker

MIGRATION_GUIDE_URL = "https://lsp.sublimetext.io/migrating_to_lsp_plugin/"

# Deprecated base classes for LSP handlers, by the module they are imported from, with a hint about what to use instead.
DEPRECATED_BASES = {
    "LSP.plugin": {
        "AbstractPlugin": "'LspPlugin'",
    },
    "lsp_utils": {
        "ClientHandler": "'LspPlugin'",
        "GenericClientHandler": "'LspPlugin'",
        "NpmClientHandler": "'LspPlugin' with lsp_utils' 'NodeManager'",
        "PipClientHandler": "'LspPlugin' with lsp_utils' 'UvVenvManager'",
    },
}


class LspCheckLspPlugin(AstChecker):
    """Checks that LSP-* packages implement their handlers using `LspPlugin` instead of the deprecated `AbstractPlugin`.

    Covers direct subclasses of `AbstractPlugin` and the lsp_utils client handlers that are based on it.
    """

    def check(self) -> None:
        if not self.package_name or not self.package_name.startswith("LSP-"):
            return
        super().check()

    def visit_Module(self, node: ast.Module) -> None:
        # Names (and aliases) of deprecated base classes imported in the current module, with the replacement hint.
        self._imported_bases: dict[str, tuple[str, str]] = {}
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for module, bases in DEPRECATED_BASES.items():
            if node.module != module and not (node.module or "").startswith(f"{module}."):
                continue
            for alias in node.names:
                if alias.name in bases:
                    self._imported_bases[alias.asname or alias.name] = (alias.name, bases[alias.name])

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for base in node.bases:
            deprecated = self._deprecated_base(base)
            if deprecated is None:
                continue
            name, replacement = deprecated
            with self.node_context(node):
                self.warn(f"Class {node.name!r} is based on the deprecated {name!r}. Implement it using {replacement} "
                          f"instead. See {MIGRATION_GUIDE_URL}")
        self.generic_visit(node)

    def _deprecated_base(self, base: ast.expr) -> tuple[str, str] | None:
        if isinstance(base, ast.Name):
            return self._imported_bases.get(base.id)
        if isinstance(base, ast.Attribute):
            # For example `lsp_utils.NpmClientHandler` after `import lsp_utils`.
            module = ast.unparse(base.value)
            for deprecated_module, bases in DEPRECATED_BASES.items():
                if base.attr in bases and (module == deprecated_module or module.startswith(f"{deprecated_module}.")):
                    return base.attr, bases[base.attr]
        return None
