import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    def test_required_fields(self):
        for key in (
            "required_api_version",
            "name",
            "description",
            "developer_name",
            "icon",
            "preferences",
        ):
            self.assertIn(key, self.manifest)

    def test_preference_ids_and_types(self):
        preferences = self.manifest["preferences"]
        ids = [preference["id"] for preference in preferences]
        self.assertEqual(len(ids), len(set(ids)))
        for preference in preferences:
            self.assertIn(preference["type"], {"text", "keyword", "select", "input"})
            self.assertTrue(preference["name"])

    def test_expected_preferences(self):
        ids = {preference["id"] for preference in self.manifest["preferences"]}
        self.assertEqual(
            ids,
            {
                "project_paths",
                "preferred_ides",
                "custom_ides",
                "terminal_command",
                "keyword_projects",
            },
        )

    def test_old_preferences_are_gone(self):
        ids = {preference["id"] for preference in self.manifest["preferences"]}
        for old_id in (
            "cursor_command",
            "ide_command",
            "keyword_cursor",
            "keyword_code",
            "keyword_zed",
            "keyword_ide",
        ):
            self.assertNotIn(old_id, ids)

    def test_keyword_has_default(self):
        keyword = next(p for p in self.manifest["preferences"] if p["type"] == "keyword")
        self.assertEqual(keyword["default_value"], "projects")

    def test_icon_files_exist(self):
        self.assertTrue((ROOT / self.manifest["icon"]).is_file())
        self.assertTrue((ROOT / "images" / "icon-disabled.png").is_file())


if __name__ == "__main__":
    unittest.main()
