import os
import tempfile
import unittest
from unittest.mock import patch

from project_launcher.config import (
    build_settings,
    parse_custom_ides,
    parse_preferred_ides,
    parse_project_paths,
    parse_terminal_command,
    slugify,
)


class ConfigTests(unittest.TestCase):
    def test_parse_project_paths_expands_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as home:
            env = {"HOME": home, "PROJECTS_ROOT": "/tmp/projetos"}
            with patch.dict(os.environ, env, clear=False):
                paths = parse_project_paths(" $PROJECTS_ROOT/api , ~/web, $PROJECTS_ROOT/api ")
            self.assertEqual(len(paths), 2)
            self.assertEqual(paths[0], "/tmp/projetos/api")
            self.assertEqual(paths[1], os.path.join(home, "web"))

    def test_parse_project_paths_empty(self):
        self.assertEqual(parse_project_paths("  ,  "), ())

    def test_parse_preferred_ides_preserves_order_and_deduplicates(self):
        self.assertEqual(
            parse_preferred_ides(" cursor, Zed, cursor , , code "),
            ("cursor", "Zed", "code"),
        )

    def test_parse_custom_ides_gui_and_cli(self):
        entries = parse_custom_ides(
            "Meu IDE=/opt/meuide/meuide --new-window; "
            "MeuAgente=terminal:meuagente --flag valor"
        )
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].name, "Meu IDE")
        self.assertEqual(entries[0].kind, "gui")
        self.assertEqual(entries[0].command, ("/opt/meuide/meuide", "--new-window"))
        self.assertEqual(entries[1].name, "MeuAgente")
        self.assertEqual(entries[1].kind, "cli")
        self.assertEqual(entries[1].command, ("meuagente", "--flag", "valor"))

    def test_parse_custom_ides_derives_name_and_ids(self):
        entries = parse_custom_ides("/usr/bin/foo; /usr/bin/foo --bar")
        self.assertEqual(entries[0].name, "foo")
        self.assertEqual(entries[1].name, "foo")
        self.assertNotEqual(entries[0].id, entries[1].id)

    def test_parse_custom_ides_ignores_invalid(self):
        entries = parse_custom_ides('SemComando="; =; ')
        self.assertEqual(entries, ())

    def test_parse_terminal_command(self):
        self.assertEqual(
            parse_terminal_command("gnome-terminal --working-directory={path} --"),
            ("gnome-terminal", "--working-directory={path}", "--"),
        )
        self.assertIsNone(parse_terminal_command("   "))
        self.assertIsNone(parse_terminal_command("'sem fechamento"))

    def test_build_settings(self):
        settings = build_settings(
            {
                "project_paths": "/tmp/a,/tmp/b",
                "preferred_ides": "cursor,zed",
                "custom_ides": "Agente=terminal:codex",
                "terminal_command": "",
            }
        )
        self.assertEqual(settings.project_paths, ("/tmp/a", "/tmp/b"))
        self.assertEqual(settings.preferred_ides, ("cursor", "zed"))
        self.assertEqual(len(settings.custom_ides), 1)
        self.assertIsNone(settings.terminal_command)

    def test_slugify(self):
        self.assertEqual(slugify("Meu IDE Ágil!"), "meu-ide-agil")
        self.assertEqual(slugify("!!!"), "ide")


if __name__ == "__main__":
    unittest.main()
