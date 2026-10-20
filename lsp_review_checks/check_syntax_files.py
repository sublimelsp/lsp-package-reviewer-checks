import re

from st_package_reviewer.check.file import FileChecker

# A top-level `hidden: true` key. Top-level keys of the YAML mapping start at the first column, so a line-based match is
# enough and avoids depending on a YAML parser that the reviewer's environment does not provide.
HIDDEN_RE = re.compile(r"^hidden[ \t]*:[ \t]*(?:true|True|TRUE)[ \t]*(?:#.*)?$", re.MULTILINE)

PACKAGE_CONTROL_CHANNEL_URL = "https://github.com/sublimehq/package_control_channel"


class LspCheckSyntaxFiles(FileChecker):
    """Checks that packages don't ship syntaxes that should rather be provided by a dedicated package.

    Hidden syntaxes (with a top-level `hidden: true`) are allowed since they are only used internally, for example for
    output panels or popups.
    """

    def check(self) -> None:
        for path in self.glob("**/*.sublime-syntax"):
            with self.file_context(path):
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue  # Reported by the resource file validity checks.
                if HIDDEN_RE.search(text):
                    continue
                self.warn("The package provides a syntax that is not hidden. Consider moving it to a dedicated package "
                          f"and submitting that to the default Package Control channel ({PACKAGE_CONTROL_CHANNEL_URL}) "
                          "so that it can be used without the language server. If the syntax is only used internally, "
                          "set 'hidden: true' in it.")
