import os
import stat
import tempfile
import unittest

from project_launcher.catalog import CATALOG
from project_launcher.detect import IdeDetector, parse_desktop_entry, parse_exec_line
from project_launcher.models import CatalogIde, CustomIde
from project_launcher.terminal import TerminalInfo


def write_executable(path):
    with open(path, "w", encoding="utf-8") as file:
        file.write("#!/bin/sh\nexit 0\n")
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)


def write_desktop(directory, filename, content):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, filename), "w", encoding="utf-8") as file:
        file.write(content)


class DetectTests(unittest.TestCase):
    def test_path_detection_and_cli_without_terminal(self):
        catalog = (
            CatalogIde(id="fakegui", name="Fake GUI", kind="gui", commands=("fakegui",), popularity=1),
            CatalogIde(id="fakecli", name="Fake CLI", kind="cli", commands=("fakecli",), popularity=2),
        )
        which = lambda name: "/bin/true" if name == "fakecli" else None
        detector = IdeDetector(catalog=catalog, desktop_dirs=[], which=which, extra_dirs=())

        options = detector.detect((), TerminalInfo(False, None, None))
        by_id = {option.id: option for option in options}
        self.assertFalse(by_id["fakegui"].installed)
        self.assertEqual(by_id["fakegui"].blocked_reason, "not_installed")
        self.assertTrue(by_id["fakecli"].installed)
        self.assertEqual(by_id["fakecli"].blocked_reason, "no_terminal")
        self.assertFalse(by_id["fakecli"].available)

    def test_cli_available_when_terminal_exists(self):
        catalog = (
            CatalogIde(id="fakecli", name="Fake CLI", kind="cli", commands=("fakecli",), popularity=1),
        )
        which = lambda name: "/bin/true" if name == "fakecli" else None
        detector = IdeDetector(catalog=catalog, desktop_dirs=[], which=which, extra_dirs=())
        terminal = TerminalInfo(True, "fake", ("/bin/true",))

        options = detector.detect((), terminal)
        self.assertTrue(options[0].available)

    def test_desktop_entry_detection(self):
        with tempfile.TemporaryDirectory() as root:
            executable = os.path.join(root, "fakeide")
            write_executable(executable)
            applications = os.path.join(root, "applications")
            write_desktop(
                applications,
                "fakeide.desktop",
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=Fake IDE\n"
                f"Exec={executable} %U\n"
                f"TryExec={executable}\n",
            )
            catalog = (
                CatalogIde(
                    id="fakeide",
                    name="Fake IDE",
                    kind="gui",
                    commands=("fakeide",),
                    desktop_ids=("fakeide",),
                    popularity=1,
                ),
            )
            detector = IdeDetector(
                catalog=catalog,
                home=root,
                desktop_dirs=[applications],
                which=lambda name: None,
                extra_dirs=(),
            )

            options = detector.detect((), TerminalInfo(False, None, None))
            self.assertEqual(len(options), 1)
            self.assertTrue(options[0].installed)
            self.assertEqual(options[0].source, "desktop")
            self.assertEqual(options[0].command, (executable,))

    def test_desktop_nodisplay_and_terminal_are_ignored(self):
        with tempfile.TemporaryDirectory() as root:
            executable = os.path.join(root, "fakeide")
            write_executable(executable)
            applications = os.path.join(root, "applications")
            write_desktop(
                applications,
                "fakeide.desktop",
                "[Desktop Entry]\n"
                "Name=Fake IDE\n"
                f"Exec={executable}\n"
                "NoDisplay=true\n"
                "Terminal=true\n",
            )
            catalog = (
                CatalogIde(
                    id="fakeide",
                    name="Fake IDE",
                    kind="gui",
                    commands=("fakeide",),
                    desktop_ids=("fakeide",),
                    popularity=1,
                ),
            )
            detector = IdeDetector(catalog=catalog, home=root, desktop_dirs=[applications], which=lambda name: None, extra_dirs=())
            options = detector.detect((), TerminalInfo(False, None, None))
            self.assertFalse(options[0].installed)

    def test_cli_is_not_matched_by_desktop_entry(self):
        with tempfile.TemporaryDirectory() as root:
            executable = os.path.join(root, "opencode")
            write_executable(executable)
            applications = os.path.join(root, "applications")
            write_desktop(
                applications,
                "opencode.desktop",
                "[Desktop Entry]\n"
                "Name=OpenCode\n"
                f"Exec={executable}\n",
            )
            catalog = (
                CatalogIde(
                    id="opencode",
                    name="OpenCode",
                    kind="cli",
                    commands=("opencode",),
                    desktop_ids=("opencode",),
                    popularity=1,
                ),
            )
            detector = IdeDetector(catalog=catalog, home=root, desktop_dirs=[applications], which=lambda name: None, extra_dirs=())
            options = detector.detect((), TerminalInfo(True, "fake", ("/bin/true",)))
            self.assertFalse(options[0].installed)

    def test_custom_overrides_catalog_and_missing_is_blocked(self):
        with tempfile.TemporaryDirectory() as root:
            catalog = (
                CatalogIde(id="fakegui", name="Fake GUI", kind="gui", commands=("fakegui",), popularity=1),
            )
            custom = CustomIde(id="custom-fake", name="Fake GUI", kind="gui", command=("/bin/true",))
            detector = IdeDetector(catalog=catalog, home=root, desktop_dirs=[], which=lambda name: None, extra_dirs=())
            options = detector.detect((custom,), TerminalInfo(False, None, None))
            self.assertEqual(len(options), 1)
            self.assertEqual(options[0].id, "custom-fake")
            self.assertTrue(options[0].available)

            missing = CustomIde(id="custom-missing", name="Missing", kind="gui", command=("missing-command-xyz",))
            options = detector.detect((missing,), TerminalInfo(False, None, None))
            self.assertFalse(options[0].installed)
            self.assertEqual(options[0].blocked_reason, "not_installed")

    def test_known_path_detection(self):
        with tempfile.TemporaryDirectory() as root:
            executable = os.path.join(root, "fakeide")
            write_executable(executable)
            catalog = (
                CatalogIde(
                    id="fakeide",
                    name="Fake IDE",
                    kind="gui",
                    commands=("fakeide",),
                    known_paths=(executable,),
                    popularity=1,
                ),
            )
            detector = IdeDetector(catalog=catalog, home=root, desktop_dirs=[], which=lambda name: None, extra_dirs=())
            options = detector.detect((), TerminalInfo(False, None, None))
            self.assertTrue(options[0].installed)
            self.assertEqual(options[0].source, "path")

    def test_parse_exec_line_strips_field_codes(self):
        self.assertEqual(parse_exec_line("/bin/true %U"), ("/bin/true",))
        self.assertIsNone(parse_exec_line(""))
        self.assertIsNone(parse_exec_line("comando-que-nao-existe-xyz %U"))

    def test_parse_desktop_entry(self):
        with tempfile.TemporaryDirectory() as root:
            executable = os.path.join(root, "fakeide")
            write_executable(executable)
            path = os.path.join(root, "fakeide.desktop")
            write_desktop(
                root,
                "fakeide.desktop",
                "[Desktop Entry]\n"
                "Name=Fake IDE\n"
                f"Exec={executable} --new-window %U\n",
            )
            entry = parse_desktop_entry(path)
            self.assertIsNotNone(entry)
            self.assertEqual(entry.name, "Fake IDE")
            self.assertEqual(entry.command, (executable, "--new-window"))

    def test_real_catalog_still_has_popular_entries(self):
        # Sanidade: o catálogo padrão continua sendo usado por padrão.
        detector = IdeDetector(catalog=CATALOG, desktop_dirs=[], which=lambda name: None, extra_dirs=())
        options = detector.detect((), TerminalInfo(False, None, None))
        names = {option.name for option in options}
        self.assertIn("Cursor", names)
        self.assertIn("Zed", names)
        self.assertIn("Visual Studio Code", names)
        self.assertIn("Codex CLI", names)


if __name__ == "__main__":
    unittest.main()
