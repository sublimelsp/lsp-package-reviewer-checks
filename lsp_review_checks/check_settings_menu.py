from st_package_reviewer.check.file.check_resource_files import CheckSettingsMenuEntry
from st_package_reviewer.lib import jsonc

# Path of menu ids under which LSP-* packages register their settings entry.
LSP_SERVERS_MENU_PATH = ("preferences", "package-settings", "lsp-settings", "lsp-servers")


class LspCheckSettingsMenu(CheckSettingsMenuEntry):
    """Replacement for the stock `CheckSettingsMenuEntry` that understands LSP conventions.

    LSP-* packages register their settings under
    `Preferences > Package Settings > LSP > Servers > <package>` instead of
    `Preferences > Package Settings > <package>`. Other packages fall back to the stock check.

    Run with `--exclude CheckSettingsMenuEntry` so that the stock check does not also run.
    """

    def check(self):
        if not self.package_name or not self.package_name.startswith("LSP-"):
            super().check()
            return

        settings_name = f"{self.package_name}.sublime-settings"
        if not self.sub_path(settings_name).is_file():
            return

        menu_path = self.sub_path("Main.sublime-menu")
        if not menu_path.is_file():
            self.warn(f"Package defines '{settings_name}' but is missing 'Main.sublime-menu' with an entry under "
                      f"'Preferences > Package Settings > LSP > Servers' to edit it.")
            return

        with self.file_context(menu_path):
            try:
                menu = jsonc.loads(menu_path.read_text(encoding="utf-8"))
            except ValueError:
                return  # Reported by the resource file validity checks.

            servers = _find_menu_node(menu, LSP_SERVERS_MENU_PATH)
            entry = next((child for child in _children(servers) if child.get("caption") == self.package_name), None)
            if entry is None:
                self.warn(f"'Main.sublime-menu' has no entry for {self.package_name!r} under "
                          f"'Preferences > Package Settings > LSP > Servers' "
                          f"(menu ids: {', '.join(LSP_SERVERS_MENU_PATH)})")
                return

            if entry.get("command") != "edit_settings":
                self.warn(f"The {self.package_name!r} settings menu entry should use the 'edit_settings' command")
                return

            expected_base_file = f"${{packages}}/{self.package_name}/{settings_name}"
            args = entry.get("args")
            base_file = args.get("base_file") if isinstance(args, dict) else None
            if base_file != expected_base_file:
                self.warn(f"The {self.package_name!r} settings menu entry should have 'base_file' set to "
                          f"{expected_base_file!r}, found {base_file!r}")


def _children(node):
    children = node.get("children") if isinstance(node, dict) else node
    return [child for child in children if isinstance(child, dict)] if isinstance(children, list) else []


def _find_menu_node(menu, ids):
    node = menu
    for menu_id in ids:
        node = next((child for child in _children(node) if child.get("id") == menu_id), None)
        if node is None:
            return None
    return node
