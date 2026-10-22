import subprocess
import unittest

from project_launcher.actions import build_gui_command, open_project
from project_launcher.models import IdeOption
from project_launcher.terminal import TerminalInfo


def option(
    ide_id="code",
    name="VS Code",
    *,
    kind="gui",
    command=("/usr/bin/code",),
    available=True,
):
    return IdeOption(
        id=ide_id,
        name=name,
        kind=kind,
        command=command if available else None,
        installed=available,
        blocked_reason=None if available else "not_installed",
        source="test",
        popularity=1,
    )


class FakePopen:
    def __init__(self):
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((list(command), kwargs))


class ActionsTests(unittest.TestCase):
    def test_build_gui_command_appends_path(self):
        self.assertEqual(
            build_gui_command(option(command=("/usr/bin/code",)), "/tmp/projeto"),
            ["/usr/bin/code", "/tmp/projeto"],
        )

    def test_build_gui_command_uses_placeholder(self):
        self.assertEqual(
            build_gui_command(option(command=("/usr/bin/code", "--folder={path}")), "/tmp/projeto"),
            ["/usr/bin/code", "--folder=/tmp/projeto"],
        )

    def test_open_gui(self):
        popen = FakePopen()
        self.assertTrue(open_project(option(), "/tmp/projeto", None, popen=popen))
        command, kwargs = popen.calls[0]
        self.assertEqual(command, ["/usr/bin/code", "/tmp/projeto"])
        self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)
        self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
        self.assertTrue(kwargs["start_new_session"])
        self.assertNotIn("cwd", kwargs)

    def test_open_cli_uses_terminal(self):
        popen = FakePopen()
        terminal = TerminalInfo(
            True,
            "gnome-terminal",
            ("/usr/bin/gnome-terminal", "--working-directory={path}", "--"),
        )
        agent = option("codex", "Codex CLI", kind="cli", command=("/usr/bin/codex", "--flag"))
        self.assertTrue(open_project(agent, "/tmp/projeto", terminal, popen=popen))
        command, kwargs = popen.calls[0]
        self.assertEqual(
            command,
            [
                "/usr/bin/gnome-terminal",
                "--working-directory=/tmp/projeto",
                "--",
                "/usr/bin/codex",
                "--flag",
            ],
        )
        self.assertNotIn("cwd", kwargs)

    def test_open_cli_without_terminal_fails(self):
        popen = FakePopen()
        agent = option("codex", "Codex CLI", kind="cli", command=("/usr/bin/codex",))
        self.assertFalse(open_project(agent, "/tmp/projeto", None, popen=popen))
        self.assertEqual(popen.calls, [])

    def test_unavailable_option_is_not_opened(self):
        popen = FakePopen()
        self.assertFalse(open_project(option(available=False), "/tmp/projeto", None, popen=popen))
        self.assertEqual(popen.calls, [])

    def test_missing_executable_returns_false(self):
        class BrokenPopen:
            def __call__(self, command, **kwargs):
                raise FileNotFoundError

        self.assertFalse(open_project(option(), "/tmp/projeto", None, popen=BrokenPopen()))

    def test_path_with_spaces_is_single_argument(self):
        popen = FakePopen()
        open_project(option(), "/tmp/meu projeto", None, popen=popen)
        command, _ = popen.calls[0]
        self.assertEqual(command[-1], "/tmp/meu projeto")


if __name__ == "__main__":
    unittest.main()
