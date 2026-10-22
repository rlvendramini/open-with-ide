import unittest
from unittest.mock import patch

from project_launcher.terminal import TerminalInfo, detect_terminal


class TerminalTests(unittest.TestCase):
    def test_build_with_placeholder(self):
        info = TerminalInfo(
            True,
            "gnome-terminal",
            ("/usr/bin/gnome-terminal", "--working-directory={path}", "--"),
        )
        launch = info.build("/tmp/meu projeto", ("/usr/bin/codex",))
        self.assertEqual(
            launch.command,
            ("/usr/bin/gnome-terminal", "--working-directory=/tmp/meu projeto", "--", "/usr/bin/codex"),
        )
        self.assertIsNone(launch.cwd)

    def test_build_without_placeholder_uses_cwd(self):
        info = TerminalInfo(True, "xterm", ("/usr/bin/xterm", "-e"))
        launch = info.build("/tmp/projeto", ("/usr/bin/codex",))
        self.assertEqual(launch.command, ("/usr/bin/xterm", "-e", "/usr/bin/codex"))
        self.assertEqual(launch.cwd, "/tmp/projeto")

    def test_unavailable_build_returns_none(self):
        self.assertIsNone(TerminalInfo(False, None, None).build("/tmp", ("/bin/true",)))

    def test_configured_terminal(self):
        info = detect_terminal(
            ("/bin/true", "--working-directory={path}", "--"),
            which=lambda name: None,
            extra_dirs=(),
        )
        self.assertTrue(info.available)
        self.assertEqual(info.source, "configured")
        self.assertEqual(info.base_command[0], "/bin/true")

    def test_auto_detects_common_terminal(self):
        info = detect_terminal(
            None,
            which=lambda name: "/bin/true" if name == "gnome-terminal" else None,
            extra_dirs=(),
            env={},
        )
        self.assertTrue(info.available)
        self.assertEqual(info.name, "gnome-terminal")
        self.assertEqual(info.source, "auto")

    def test_terminal_env(self):
        info = detect_terminal(
            None,
            which=lambda name: "/bin/true" if name == "kitty" else None,
            extra_dirs=(),
            env={"TERMINAL": "kitty"},
        )
        self.assertTrue(info.available)
        self.assertEqual(info.name, "kitty")
        self.assertEqual(info.source, "env")
        self.assertEqual(info.base_command[1:], ("--directory", "{path}"))

    def test_no_terminal(self):
        with patch("project_launcher.paths.COMMON_BIN_DIRS", ()):
            info = detect_terminal(None, which=lambda name: None, extra_dirs=(), env={})
        self.assertFalse(info.available)
        self.assertIsNone(info.build("/tmp", ("/bin/true",)))


if __name__ == "__main__":
    unittest.main()
