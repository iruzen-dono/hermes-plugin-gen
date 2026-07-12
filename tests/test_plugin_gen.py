"""Tests for hermes-plugin-gen import and basic structure."""

import ast
import unittest
from pathlib import Path


class TestPluginGen(unittest.TestCase):
    """Verify the plugin Python files are syntactically valid."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_all_py_files_parse(self):
        """Every .py file in the repo must parse as valid Python."""
        py_files = list(self.repo_root.rglob("*.py"))
        self.assertGreater(len(py_files), 0, "No Python files found")

        for f in py_files:
            with self.subTest(file=f.relative_to(self.repo_root)):
                source = f.read_text(encoding="utf-8")
                ast.parse(source, filename=str(f))

    def test_plugin_yaml_exists(self):
        """plugin.yaml must exist at the root."""
        yaml_file = self.repo_root / "plugin.yaml"
        self.assertTrue(yaml_file.exists())
        self.assertGreater(yaml_file.stat().st_size, 50)

    def test_readme_exists(self):
        """README.md must exist."""
        readme = self.repo_root / "README.md"
        self.assertTrue(readme.exists())
        self.assertGreater(readme.stat().st_size, 100)

    def test_license_exists(self):
        """LICENSE must exist."""
        license_file = self.repo_root / "LICENSE"
        self.assertTrue(license_file.exists())
