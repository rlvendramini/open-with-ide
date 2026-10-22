import os
import tempfile
import unittest

from project_launcher.models import Project
from project_launcher.search import scan_projects, score_project, search_projects


def make_project(name, path=None):
    return Project(name=name, path=path or f"/tmp/{name}", base="/tmp")


class SearchTests(unittest.TestCase):
    def test_empty_query_returns_limit(self):
        projects = [make_project(f"p{i}") for i in range(15)]
        self.assertEqual(len(search_projects(projects, "")), 10)

    def test_exact_match_comes_first(self):
        projects = [
            make_project("meu-projeto-web"),
            make_project("web"),
            make_project("projeto-web"),
        ]
        results = search_projects(projects, "web")
        self.assertEqual(results[0].name, "web")

    def test_prefix_and_substring(self):
        projects = [make_project("api-client"), make_project("meu-api"), make_project("outro")]
        results = search_projects(projects, "api")
        self.assertEqual([p.name for p in results], ["api-client", "meu-api"])

    def test_accent_insensitive(self):
        projects = [make_project("Configuração")]
        results = search_projects(projects, "configuracao")
        self.assertEqual([p.name for p in results], ["Configuração"])

    def test_multiple_tokens_require_all(self):
        projects = [
            make_project("web-api"),
            make_project("web-front"),
            make_project("api-mobile"),
        ]
        results = search_projects(projects, "web api")
        self.assertEqual([p.name for p in results], ["web-api"])

    def test_subsequence(self):
        self.assertIsNotNone(score_project(make_project("projeto-web"), "prjt"))
        self.assertIsNone(score_project(make_project("projeto-web"), "xyz"))

    def test_limit(self):
        projects = [make_project(f"projeto-{i}") for i in range(20)]
        self.assertEqual(len(search_projects(projects, "projeto", limit=3)), 3)

    def test_scan_projects_with_temp_dirs(self):
        with tempfile.TemporaryDirectory() as root:
            base = os.path.join(root, "base")
            os.makedirs(os.path.join(base, "Zeta"))
            os.makedirs(os.path.join(base, "alfa"))
            os.makedirs(os.path.join(base, ".oculto"))
            with open(os.path.join(base, "arquivo.txt"), "w", encoding="utf-8") as file:
                file.write("x")

            projects = scan_projects([base])
            self.assertEqual([p.name for p in projects], [".oculto", "alfa", "Zeta"])

    def test_scan_projects_deduplicates_roots(self):
        with tempfile.TemporaryDirectory() as root:
            base = os.path.join(root, "base")
            os.makedirs(os.path.join(base, "projeto"))
            projects = scan_projects([base, base])
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0].name, "projeto")

    def test_scan_projects_ignores_missing_and_files(self):
        with tempfile.TemporaryDirectory() as root:
            base = os.path.join(root, "base")
            os.makedirs(base)
            file_path = os.path.join(root, "arquivo")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("x")
            self.assertEqual(scan_projects([base, file_path, os.path.join(root, "nada")]), ())


if __name__ == "__main__":
    unittest.main()
