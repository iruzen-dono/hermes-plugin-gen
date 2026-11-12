"""Tests for SKILL.md frontmatter generation in plugin_add_skill.

`plugin_add_skill` declares `skill_description` as a required parameter in
schemas.py. Before these tests existed, tools.py read the argument and never
used it: the description a caller was forced to provide was silently dropped.

tools.py is loaded by file path rather than added to sys.path: the repository
root carries an __init__.py (it is a Hermes plugin package), so putting it on
sys.path makes pytest treat the whole repo as a package and every test fails
with "attempted relative import with no known parent package".
"""

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("hpg_tools", REPO_ROOT / "tools.py")
_tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tools)

_ensure_skill_frontmatter = _tools._ensure_skill_frontmatter


class TestSkillFrontmatter(unittest.TestCase):
    """The description the schema requires must reach the written file."""

    def test_adds_frontmatter_when_missing(self):
        out = _ensure_skill_frontmatter("# Skill\n\nBody.", "my-skill", "What it does")
        self.assertTrue(out.startswith("---\n"))
        self.assertIn('name: "my-skill"', out)
        self.assertIn('description: "What it does"', out)
        self.assertTrue(out.endswith("# Skill\n\nBody."))

    def test_completes_existing_frontmatter(self):
        content = "---\nname: my-skill\nversion: 1.0.0\n---\n\nBody."
        out = _ensure_skill_frontmatter(content, "my-skill", "What it does")
        self.assertIn('description: "What it does"', out)
        self.assertIn("name: my-skill", out)
        self.assertIn("version: 1.0.0", out)

    def test_leaves_existing_description_untouched(self):
        content = '---\nname: my-skill\ndescription: "Already here"\n---\n\nBody.'
        out = _ensure_skill_frontmatter(content, "my-skill", "Something else")
        self.assertEqual(out, content)

    def test_empty_description_is_a_noop(self):
        content = "# Skill\n\nBody."
        self.assertEqual(_ensure_skill_frontmatter(content, "my-skill", ""), content)

    def test_description_with_colon_stays_valid_yaml(self):
        out = _ensure_skill_frontmatter("Body.", "s", "Handles: quoting and billing")
        self.assertIn('description: "Handles: quoting and billing"', out)

    def test_unterminated_frontmatter_is_left_alone(self):
        content = "---\nname: x\nBody without closing fence."
        self.assertEqual(_ensure_skill_frontmatter(content, "x", "desc"), content)


if __name__ == "__main__":
    unittest.main()
