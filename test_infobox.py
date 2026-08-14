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
  <figure><img src="./Example — Grokipedia_files/hero.jpg" alt="Example Person"><figcaption>Portrait of Example Person</figcaption></figure>
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
| Caption | Portrait of Example Person |
| Birth Date | January 1, 1900 |
| Nationality | One, Two |
| Field | Physics \\| Mathematics |"""
        self.assertIn(expected, md)
        self.assertNotIn("Example PersonBirth Date", md)
        self.assertIn("Opening paragraph.[^1]", md)

    def test_caption_uses_inline_markdown(self):
        html = r'''<!doctype html><html><body><article><div class="flow-root">
        <div><h1>Caption Test</h1></div>
        <aside><figure><img src="https://example.com/image.jpg" alt="Alt text">
        <figcaption>An <em>illustrated</em> <a href="https://example.com/source">caption</a></figcaption>
        </figure><dt>Type</dt><dd>Example</dd></aside>
        </div></article></body></html>'''
        md = convert_html(html)
        self.assertIn(
            "| Caption | An *illustrated* [caption](https://example.com/source) |",
            md,
        )


if __name__ == "__main__":
    unittest.main()


class AdditionalLayoutTests(unittest.TestCase):
    def test_infobox_without_image_is_still_a_table(self):
        html = r'''<!doctype html><html><body><article><div class="flow-root">
        <div><h1>Event</h1></div>
        <aside><div><dt>Date</dt><dd>1939–1945</dd></div>
        <div><dt>Sides</dt><dd><div><span>Allies</span><span>Axis</span></div></dd></div></aside>
        <span>Opening text.</span>
        </div></article></body></html>'''
        md = convert_html(html)
        self.assertIn("| Attribute | Value |", md)
        self.assertIn("| Date | 1939–1945 |", md)
        self.assertIn("| Sides | Allies, Axis |", md)
        self.assertNotIn("| Image |", md)
        self.assertIn("Opening text.", md)

    def test_article_figure_keeps_image_and_caption(self):
        html = r'''<!doctype html><html><head>
        <link rel="canonical" href="https://grokipedia.com/page/Event">
        <meta property="og:image" content="https://assets.grokipedia.com/wiki/images/hero.jpg">
        </head><body><article><div class="flow-root">
        <div><h1>Event</h1></div>
        <h2>Background</h2>
        <figure><img src="./Event — Grokipedia_files/photo.jpg" alt="A scene">
        <figcaption>A <em>descriptive</em> <a href="https://example.com">caption</a></figcaption></figure>
        <span>Text after the figure.</span>
        </div></article></body></html>'''
        md = convert_html(html)
        self.assertIn(
            "![A scene](https://assets.grokipedia.com/wiki/images/photo.jpg)", md
        )
        self.assertIn(
            "*Caption:* A *descriptive* [caption](https://example.com)", md
        )
        self.assertLess(md.index("![A scene]"), md.index("Text after the figure."))


class SectionedInfoboxTests(unittest.TestCase):
    def test_sectioned_infobox_becomes_separate_heading_tables(self):
        html = r'''<!doctype html><html><head>
        <meta property="og:image" content="https://assets.grokipedia.com/wiki/images/person.jpg">
        </head><body><article><div class="flow-root">
        <div><h1>Office Holder</h1></div>
        <aside>
          <figure><img src="./Office Holder — Grokipedia_files/person.jpg" alt="Portrait">
          <figcaption>Official portrait</figcaption></figure>
          <div class="flex flex-col">
            <div class="flex flex-col">
              <div class="text-xs font-bold uppercase tracking-wider">First Office</div>
              <div><dt>Term</dt><dd>2000–2005</dd></div>
              <div><dt>Predecessor</dt><dd>Person A</dd></div>
            </div>
            <div class="flex flex-col">
              <div class="text-xs font-bold uppercase tracking-wider">Second Office</div>
              <div><dt>Term</dt><dd>1995–2000</dd></div>
              <div><dt>Successor</dt><dd>Person B</dd></div>
            </div>
          </div>
        </aside>
        <span>Opening text.</span>
        </div></article></body></html>'''
        md = convert_html(html)

        self.assertIn("| Image | ![Portrait](https://assets.grokipedia.com/wiki/images/person.jpg) |", md)
        self.assertIn("| Caption | Official portrait |", md)
        self.assertIn("### First Office", md)
        self.assertIn("### Second Office", md)
        first = md.index("### First Office")
        second = md.index("### Second Office")
        self.assertLess(first, second)
        self.assertIn("| Term | 2000–2005 |", md[first:second])
        self.assertIn("| Predecessor | Person A |", md[first:second])
        self.assertIn("| Term | 1995–2000 |", md[second:])
        self.assertIn("| Successor | Person B |", md[second:])
        self.assertEqual(md.count("### First Office"), 1)
        self.assertEqual(md.count("### Second Office"), 1)
