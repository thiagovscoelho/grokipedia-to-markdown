import unittest

from grokipedia_to_markdown import convert_html


SAMPLE = r'''<!doctype html>
<html><head><link rel="canonical" href="https://grokipedia.com/page/Test"></head><body>
<article><div class="flow-root">
<div><h1>Test Article</h1><button>Listen</button></div>
<span data-tts-block="true">A sentence.<sup><a href="https://grokipedia.com/page/Test#ref-1">[1]</a></sup><sup><a href="#ref-2">[2]</a></sup></span>
<h2 id="section">Section</h2>
<span data-tts-block="true">Text with <em>emphasis</em> and <a href="/page/Other">a link</a>.</span>
<div id="references"><h2>References</h2><ol>
<li id="ref-1"><div><a href="https://example.com/one">Source One</a></div></li>
<li id="ref-2"><div><a href="https://example.com/two">Source Two</a></div></li>
</ol></div>
</div></article></body></html>'''


class ConverterTests(unittest.TestCase):
    def test_basic_conversion_and_footnotes(self):
        md = convert_html(SAMPLE)
        self.assertIn("# Test Article", md)
        self.assertIn("A sentence.[^1][^2]", md)
        self.assertIn("## Section", md)
        self.assertIn("Text with *emphasis* and [a link](https://grokipedia.com/page/Other).", md)
        self.assertIn("[^1]: [Source One](https://example.com/one)", md)
        self.assertIn("[^2]: [Source Two](https://example.com/two)", md)
        self.assertNotIn("## References", md)


if __name__ == "__main__":
    unittest.main()
