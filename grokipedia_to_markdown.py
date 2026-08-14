#!/usr/bin/env python3
"""Grokipedia to Markdown.

Convert a Grokipedia article (live URL or saved HTML file) to readable Markdown,
with Grokipedia citations represented as Markdown footnotes.
"""

from __future__ import annotations

import argparse
import html as html_lib
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

try:
    from bs4 import BeautifulSoup, NavigableString, Tag
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency: beautifulsoup4. Install it with:\n"
        "  python -m pip install beautifulsoup4"
    ) from exc


USER_AGENT = "Grokipedia-to-Markdown/1.0 (+https://grokipedia.com/)"
REF_RE = re.compile(r"#ref-(\d+)(?:$|[?&])")
REF_ID_RE = re.compile(r"^ref-(\d+)$")
WHITESPACE_RE = re.compile(r"\s+")


def read_source(source: str) -> tuple[str, str | None]:
    """Return (HTML, source URL if known)."""
    parsed = urlparse(source)
    if parsed.scheme in {"http", "https"}:
        req = Request(source, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace"), source

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"No such file: {source}")
    return path.read_text(encoding="utf-8", errors="replace"), None


def canonical_url(soup: BeautifulSoup, fallback: str | None) -> str | None:
    link = soup.find("link", rel="canonical")
    if isinstance(link, Tag) and link.get("href"):
        return str(link["href"])
    return fallback


def collapse_inline_whitespace(text: str) -> str:
    return WHITESPACE_RE.sub(" ", html_lib.unescape(text))


def escape_link_text(text: str) -> str:
    # Escaping [] is enough to keep labels such as "[PDF] ..." valid.
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def escape_inline_code(text: str) -> str:
    if "`" not in text:
        return f"`{text}`"
    longest = max((len(m.group(0)) for m in re.finditer(r"`+", text)), default=0)
    fence = "`" * (longest + 1)
    return f"{fence} {text} {fence}"


class Converter:
    def __init__(self, soup: BeautifulSoup, base_url: str | None = None):
        self.soup = soup
        self.base_url = base_url
        self.cited: set[int] = set()
        self.references = self._collect_references()

    def _collect_references(self) -> dict[int, Tag]:
        refs: dict[int, Tag] = {}
        for li in self.soup.find_all("li", id=REF_ID_RE):
            match = REF_ID_RE.match(str(li.get("id", "")))
            if match:
                refs[int(match.group(1))] = li
        return refs

    def _citation_number(self, tag: Tag) -> int | None:
        # Citation wrappers can contain duplicate anchors; one footnote marker per
        # outer <sup> is the intended representation.
        for a in tag.find_all("a", href=True):
            match = REF_RE.search(str(a["href"]))
            if match:
                return int(match.group(1))
        return None

    def inline(self, node) -> str:
        if isinstance(node, NavigableString):
            return collapse_inline_whitespace(str(node))
        if not isinstance(node, Tag):
            return ""

        name = node.name.lower()

        if name == "sup":
            n = self._citation_number(node)
            if n is not None:
                self.cited.add(n)
                return f"[^{n}]"
            body = self.inline_children(node).strip()
            return f"^{body}^" if body else ""

        if name in {"em", "i"}:
            body = self.inline_children(node).strip()
            return f"*{body}*" if body else ""

        if name in {"strong", "b"}:
            body = self.inline_children(node).strip()
            return f"**{body}**" if body else ""

        if name == "code":
            return escape_inline_code(node.get_text("", strip=False))

        if name == "br":
            return "  \n"

        if name == "a":
            href = node.get("href")
            label = self.inline_children(node).strip()
            if not href or not label:
                return label
            # Citation anchors are handled by their enclosing <sup>. If one
            # appears bare, still convert it to a footnote marker.
            match = REF_RE.search(str(href))
            if match:
                n = int(match.group(1))
                self.cited.add(n)
                return f"[^{n}]"
            absolute = urljoin(self.base_url or "", str(href))
            return f"[{escape_link_text(label)}]({absolute})"

        # UI-only elements should never leak into prose.
        if name in {"button", "svg", "script", "style", "noscript"}:
            return ""

        return self.inline_children(node)

    def inline_children(self, tag: Tag) -> str:
        return "".join(self.inline(child) for child in tag.children)

    def clean_paragraph(self, text: str) -> str:
        text = text.strip()
        # Remove HTML formatting whitespace before punctuation and footnotes.
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)
        text = re.sub(r"\s+(?=\[\^\d+\])", "", text)
        text = re.sub(r"(\[\^\d+\])\s+(?=\[\^\d+\])", r"\1", text)
        text = re.sub(r"\(\s+", "(", text)
        text = re.sub(r"\s+\)", ")", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text

    def block(self, tag: Tag) -> str:
        name = tag.name.lower()
        if tag.get("id") == "references":
            return ""
        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = int(name[1])
            return f"{'#' * level} {self.clean_paragraph(self.inline_children(tag))}"
        if name in {"p", "span"}:
            return self.clean_paragraph(self.inline_children(tag))
        if name == "blockquote":
            body = self.clean_paragraph(self.inline_children(tag))
            return "\n".join(f"> {line}" if line else ">" for line in body.splitlines())
        if name in {"ul", "ol"}:
            return self.list_block(tag)
        if name == "pre":
            text = tag.get_text("", strip=False).rstrip("\n")
            fence = "```"
            if "```" in text:
                fence = "````"
            return f"{fence}\n{text}\n{fence}"
        if name == "hr":
            return "---"
        if name == "table":
            return self.table_block(tag)
        if name == "img":
            src = tag.get("src")
            alt = tag.get("alt", "")
            if src:
                return f"![{escape_link_text(str(alt))}]({urljoin(self.base_url or '', str(src))})"
            return ""

        # For containers, convert meaningful direct children rather than dumping
        # interface text. This helps with future Grokipedia layouts.
        parts = []
        for child in tag.children:
            if isinstance(child, Tag):
                converted = self.block(child)
                if converted:
                    parts.append(converted)
        return "\n\n".join(parts)

    def list_block(self, tag: Tag, depth: int = 0) -> str:
        ordered = tag.name.lower() == "ol"
        lines: list[str] = []
        index = 1
        for li in tag.find_all("li", recursive=False):
            marker = f"{index}." if ordered else "-"
            index += 1
            chunks: list[str] = []
            nested: list[Tag] = []
            for child in li.children:
                if isinstance(child, Tag) and child.name.lower() in {"ul", "ol"}:
                    nested.append(child)
                else:
                    chunks.append(self.inline(child))
            text = self.clean_paragraph("".join(chunks))
            lines.append(f"{'  ' * depth}{marker} {text}")
            for sub in nested:
                lines.append(self.list_block(sub, depth + 1))
        return "\n".join(lines)

    def table_block(self, table: Tag) -> str:
        rows: list[list[str]] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"], recursive=False)
            if cells:
                rows.append([self.clean_paragraph(self.inline_children(c)).replace("|", "\\|") for c in cells])
        if not rows:
            return ""
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        header = rows[0]
        body = rows[1:]
        out = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
        out.extend("| " + " | ".join(r) + " |" for r in body)
        return "\n".join(out)

    def reference_definition(self, number: int, li: Tag) -> str:
        container = li.find("div") or li
        rendered = self.clean_paragraph(self.inline_children(container))
        if not rendered:
            rendered = self.clean_paragraph(li.get_text(" ", strip=True))
        return f"[^{number}]: {rendered}"

    def convert(self) -> str:
        article = self.soup.find("article")
        if not isinstance(article, Tag):
            raise ValueError("Could not find a Grokipedia <article> element in the HTML.")

        title_tag = article.find("h1")
        if not isinstance(title_tag, Tag):
            title_tag = self.soup.find("h1")
        if not isinstance(title_tag, Tag):
            raise ValueError("Could not find the article title (<h1>).")
        title = self.clean_paragraph(self.inline_children(title_tag))

        flow = article.find("div", class_=lambda c: c and "flow-root" in (c if isinstance(c, list) else str(c).split()))
        root = flow if isinstance(flow, Tag) else article

        blocks: list[str] = [f"# {title}"]
        for child in root.children:
            if not isinstance(child, Tag):
                continue
            if child.get("id") == "references":
                break
            # The first layout div contains the H1 plus playback/copy controls.
            if child.find("h1") is not None:
                continue
            # Grokipedia inserts layout clearers with no text.
            if child.name == "div" and not child.get_text(" ", strip=True):
                continue
            converted = self.block(child)
            if converted:
                blocks.append(converted)

        # Definitions are numeric to mirror Grokipedia's reference IDs.
        footnotes: list[str] = []
        missing: list[int] = []
        for number in sorted(self.cited):
            li = self.references.get(number)
            if li is None:
                missing.append(number)
                continue
            footnotes.append(self.reference_definition(number, li))

        if missing:
            # Keep unresolved citations valid rather than silently deleting them.
            for number in missing:
                footnotes.append(f"[^{number}]: Reference {number} was not present in the saved HTML.")

        result = "\n\n".join(blocks)
        if footnotes:
            result += "\n\n" + "\n".join(footnotes)
        return result.rstrip() + "\n"


def convert_html(html: str, source_url: str | None = None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    base = canonical_url(soup, source_url)
    return Converter(soup, base_url=base).convert()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Grokipedia to Markdown",
        description="Convert a Grokipedia article URL or saved HTML file to Markdown with footnote citations.",
    )
    parser.add_argument("source", help="Grokipedia URL or path to a saved .html file")
    parser.add_argument("-o", "--output", help="Write Markdown to this file instead of stdout")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        html, fetched_url = read_source(args.source)
        markdown = convert_html(html, fetched_url)
        if args.output:
            Path(args.output).write_text(markdown, encoding="utf-8")
        else:
            sys.stdout.write(markdown)
        return 0
    except Exception as exc:
        print(f"grokipedia-to-markdown: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
