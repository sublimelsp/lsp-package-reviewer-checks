from st_package_reviewer.check.file import FileChecker
from st_package_reviewer.lib import jsonc

from .json_types import JsonValue

# Deprecated ClientConfig keys (see LSP's sublime-package.json) and their replacements.
DEPRECATED_KEYS = {
    "initializationOptions": "Use 'initialization_options' instead.",
    "ignore_server_trigger_chars": "Use 'disabled_capabilities' instead: "
                                   "{\"completionProvider\": {\"triggerCharacters\": true}}.",
}

# ClientConfig keys that should only be specified when they contain any keys.
NON_EMPTY_OBJECT_KEYS = ("initialization_options", "settings")


class LspCheckSettingsFile(FileChecker):
    """Checks the `<package>.sublime-settings` file of LSP-* packages for redundant and deprecated keys."""

    def check(self) -> None:
        if not self.package_name or not self.package_name.startswith("LSP-"):
            return

        settings_name = f"{self.package_name}.sublime-settings"
        settings_path = self.sub_path(settings_name)
        if not settings_path.is_file():
            return

        with self.file_context(settings_path):
            try:
                settings: JsonValue = jsonc.loads(settings_path.read_text(encoding="utf-8"))
            except ValueError:
                return  # Reported by the resource file validity checks.
            if not isinstance(settings, dict):
                return

            if "enabled" in settings and settings["enabled"] is not False:
                self.warn(f"'{settings_name}' should not specify 'enabled' unless it is set to false. "
                          f"Packages are enabled by default.")

            for key in NON_EMPTY_OBJECT_KEYS:
                value = settings.get(key)
                if key in settings and not (isinstance(value, dict) and value):
                    self.warn(f"'{settings_name}' should not specify {key!r} unless it includes any keys")

            if settings.get("schemes") == ["file"]:
                self.warn(f"'{settings_name}' should not specify 'schemes' set to [\"file\"]. It is the default value.")

            for key, replacement in DEPRECATED_KEYS.items():
                if key in settings:
                    self.warn(f"'{settings_name}' uses the deprecated {key!r} setting. {replacement}")
