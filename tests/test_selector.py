import unittest

from project_launcher.ide_service import order_options
from project_launcher.models import IdeOption
from project_launcher.selector import (
    ICON,
    ICON_DISABLED,
    LOCK_PREFIX,
    build_picker_items,
    has_available,
)


def option(ide_id, name, *, available=True, kind="gui", default=False, popularity=1):
    return IdeOption(
        id=ide_id,
        name=name,
        kind=kind,
        command=("/usr/bin/code", "--new-window") if available else None,
        installed=available,
        blocked_reason=None if available else "not_installed",
        source="test",
        popularity=popularity,
        is_default=default,
    )


class SelectorTests(unittest.TestCase):
    def test_available_items_are_enabled(self):
        items = build_picker_items([option("cursor", "Cursor", default=True)])
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0].enabled)
        self.assertEqual(items[0].ide_id, "cursor")
        self.assertEqual(items[0].icon, ICON)
        self.assertIn("IDE padrão", items[0].description)

    def test_blocked_item_is_locked_and_disabled(self):
        items = build_picker_items([option("code", "VS Code", available=False)])
        self.assertEqual(items[0].name, "Nenhuma IDE/agente instalado")
        self.assertEqual(items[1].name, f"{LOCK_PREFIX}VS Code")
        self.assertFalse(items[1].enabled)
        self.assertIsNone(items[1].ide_id)
        self.assertEqual(items[1].icon, ICON_DISABLED)
        self.assertIn("Não instalado", items[1].description)
        self.assertFalse(has_available([option("code", "VS Code", available=False)]))

    def test_cli_item_mentions_terminal(self):
        items = build_picker_items([option("codex", "Codex CLI", kind="cli")])
        self.assertIn("CLI", items[0].description)
        self.assertIn("terminal", items[0].description)
        self.assertEqual(items[0].kind, "cli")

    def test_no_terminal_reason(self):
        blocked = IdeOption(
            id="codex",
            name="Codex CLI",
            kind="cli",
            command=("/usr/bin/codex",),
            installed=True,
            blocked_reason="no_terminal",
            source="test",
            popularity=1,
        )
        items = build_picker_items([blocked])
        self.assertIn("terminal compatível", items[1].description)

    def test_warning_when_nothing_available(self):
        items = build_picker_items([option("code", "VS Code", available=False)])
        self.assertEqual(items[0].name, "Nenhuma IDE/agente instalado")
        self.assertFalse(items[0].enabled)

    def test_order_preserved(self):
        options = (
            option("cursor", "Cursor", default=True, popularity=1),
            option("code", "VS Code", available=False, popularity=2),
        )
        ordered = order_options(options, ())
        items = build_picker_items(ordered)
        self.assertEqual(items[0].name, "Cursor")
        self.assertEqual(items[1].name, f"{LOCK_PREFIX}VS Code")


if __name__ == "__main__":
    unittest.main()
