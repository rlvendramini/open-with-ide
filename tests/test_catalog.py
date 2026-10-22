import unittest

from project_launcher.catalog import CATALOG, CATALOG_BY_ID, JETBRAINS_IDS


class CatalogTests(unittest.TestCase):
    def test_ids_are_unique(self):
        ids = [entry.id for entry in CATALOG]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_popular_entries(self):
        names = {entry.name for entry in CATALOG}
        for expected in (
            "Cursor",
            "Zed",
            "Visual Studio Code",
            "Codex CLI",
            "Claude Code",
            "OpenCode",
        ):
            self.assertIn(expected, names)

    def test_commands_are_not_empty(self):
        for entry in CATALOG:
            self.assertTrue(entry.commands, entry.id)
            self.assertIn(entry.kind, {"gui", "cli"})

    def test_popularity_is_ordered(self):
        popularity = [entry.popularity for entry in CATALOG]
        self.assertEqual(popularity, list(range(1, len(CATALOG) + 1)))

    def test_by_id_matches_catalog(self):
        for entry in CATALOG:
            self.assertIs(CATALOG_BY_ID[entry.id], entry)

    def test_jetbrains_ids_exist(self):
        for ide_id in JETBRAINS_IDS:
            self.assertIn(ide_id, CATALOG_BY_ID)


if __name__ == "__main__":
    unittest.main()
