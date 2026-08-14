import unittest

from grokipedia_to_markdown import convert_html


SAMPLE = r'''<!doctype html>
<html><head>
<link rel="canonical" href="https://grokipedia.com/page/Example">
<meta property="og:image" content="https://assets.grokipedia.com/wiki/images/hero.jpg">
</head><body>
<article><div class="flow-root">
<div><h1>Example Person</h1></div>
<aside class="infobox">
  <figure><img src="./Example — Grokipedia_files/hero.jpg" alt="Example Person"></figure>
  <div>
    <div><dt>Birth Date</dt><dd>January 1, 1900</dd></div>
    <div><dt>Nationality</dt><dd><div><span>One</span><span>Two</span></div></dd></div>
    <div><dt>Field</dt><dd>Physics | Mathematics</dd></div>
  </div>
</aside>
<span>Opening paragraph.<sup><a href="#ref-1">[1]</a></sup></span>
<div id="references"><ol><li id="ref-1"><div><a href="https://example.com">Source</a></div></li></ol></div>
</div></article></body></html>'''


class InfoboxTests(unittest.TestCase):
    def test_infobox_becomes_markdown_table(self):
        md = convert_html(SAMPLE)
        expected = """| Attribute | Value |
| --- | --- |
| Image | ![Example Person](https://assets.grokipedia.com/wiki/images/hero.jpg) |
| Birth Date | January 1, 1900 |
| Nationality | One, Two |
| Field | Physics \\| Mathematics |"""
        self.assertIn(expected, md)
        self.assertNotIn("Example PersonBirth Date", md)
        self.assertIn("Opening paragraph.[^1]", md)


if __name__ == "__main__":
    unittest.main()
