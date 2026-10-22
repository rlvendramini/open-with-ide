import unittest

from project_launcher.ide_service import (
    default_option,
    find_option,
    order_options,
    resolve_preferred,
)
from project_launcher.models import IdeOption


def option(
    ide_id,
    name,
    *,
    installed=True,
    blocked_reason=None,
    popularity=10,
    command=None,
    kind="gui",
):
    return IdeOption(
        id=ide_id,
        name=name,
        kind=kind,
        command=command if command is not None else ("/bin/true",),
        installed=installed,
        blocked_reason=blocked_reason,
        source="test",
        popularity=popularity,
    )


class IdeServiceTests(unittest.TestCase):
    def test_preferred_order_and_default(self):
        options = (
            option("zed", "Zed", popularity=2),
            option("cursor", "Cursor", popularity=1),
            option("code", "VS Code", popularity=3),
        )
        ordered = order_options(options, ("zed", "cursor"))
        self.assertEqual([o.id for o in ordered], ["zed", "cursor", "code"])
        self.assertTrue(ordered[0].is_default)
        self.assertFalse(ordered[1].is_default)
        self.assertEqual(default_option(ordered).id, "zed")

    def test_blocked_items_go_last(self):
        options = (
            option("blocked", "Blocked", installed=False, blocked_reason="not_installed", popularity=0),
            option("cursor", "Cursor", popularity=5),
        )
        ordered = order_options(options, ())
        self.assertEqual([o.id for o in ordered], ["cursor", "blocked"])
        self.assertTrue(ordered[0].is_default)

    def test_blocked_preferred_falls_back(self):
        options = (
            option("zed", "Zed", installed=False, blocked_reason="not_installed", popularity=1),
            option("cursor", "Cursor", popularity=2),
        )
        ordered = order_options(options, ("zed",))
        self.assertEqual(default_option(ordered).id, "cursor")
        self.assertTrue(any(o.id == "zed" and not o.available for o in ordered))

    def test_match_by_command_basename(self):
        options = (option("vscode", "Visual Studio Code", command=("/usr/bin/code",)),)
        preferred, _ = resolve_preferred(options, ("code",))
        self.assertEqual([o.id for o in preferred], ["vscode"])

    def test_ad_hoc_preferred_path(self):
        preferred, options = resolve_preferred((), ("/bin/true",))
        self.assertEqual(len(preferred), 1)
        self.assertEqual(preferred[0].source, "preferred")
        self.assertEqual(preferred[0].name, "true")
        self.assertEqual(len(options), 1)

    def test_unknown_preferred_is_ignored(self):
        preferred, options = resolve_preferred((), ("comando-que-nao-existe-xyz",))
        self.assertEqual(preferred, [])
        self.assertEqual(options, ())

    def test_find_option(self):
        options = (option("cursor", "Cursor"),)
        self.assertEqual(find_option(options, "cursor").id, "cursor")
        self.assertIsNone(find_option(options, "missing"))
        self.assertIsNone(find_option(options, None))

    def test_only_blocked_has_no_default(self):
        options = (option("x", "X", installed=False, blocked_reason="not_installed"),)
        ordered = order_options(options, ())
        self.assertIsNone(default_option(ordered))
        self.assertFalse(ordered[0].is_default)


if __name__ == "__main__":
    unittest.main()
