import unittest

from grokipedia_gui import suggested_filename


class GUIHelperTests(unittest.TestCase):
    def test_url_filename(self):
        self.assertEqual(
            suggested_filename("https://grokipedia.com/page/Ludwig_von_Mises"),
            "ludwig-von-mises.md",
        )

    def test_file_filename(self):
        self.assertEqual(
            suggested_filename("/tmp/Ludwig von Mises — Grokipedia.html"),
            "ludwig-von-mises-grokipedia.md",
        )

    def test_markdown_title_fallback(self):
        self.assertEqual(suggested_filename("", "# Test Article\n\nBody\n"), "test-article.md")


if __name__ == "__main__":
    unittest.main()
