# Grokipedia to Markdown

A small Python program that converts a Grokipedia article into sensible Markdown and turns Grokipedia's numbered citations into Markdown footnotes.

Grokipedia infoboxes are converted to two-column Markdown tables, including
infoboxes that have no image. When a lead image is present, its image and
caption become `Image` and `Caption` rows. Compound infoboxes with titled
subsections (for example, several political offices followed by personal
details) are split into separate tables under Markdown subheadings. Images
embedded throughout the article are kept in reading order with their captions.
Browser-saved local image paths are restored to their original Grokipedia asset
URLs when the page metadata provides the asset host.

It includes both a **desktop GUI** and a **command-line interface**.

## Install

Python 3.10+ is recommended.

```bash
python -m pip install -r requirements.txt
```

The desktop GUI uses Python's built-in Tkinter library, so it adds no Python package dependency. On some Linux distributions, Tkinter is installed separately (for example, via a package such as `python3-tk`).

## Desktop GUI

### macOS / Linux

From a terminal in this folder:

```bash
./grokipedia-to-markdown-gui
```

Or:

```bash
python3 grokipedia_gui.py
```

### Windows

Double-click:

```text
grokipedia-to-markdown-gui.bat
```

Or run:

```bash
python grokipedia_gui.py
```

In the GUI you can:

- paste a live Grokipedia article URL;
- choose a previously saved `.html` page;
- preview and edit the generated Markdown;
- copy the Markdown to the clipboard; and
- save it as a `.md` file.

For an article with an infobox, output begins in this form:

```markdown
| Attribute | Value |
| --- | --- |
| Image | ![Mosaic of Jesus as the Good Shepherd with sheep](https://assets.grokipedia.com/wiki/images/1af8d74d8a5d.jpg) |
| Caption | Early Christian mosaic of Christ the Good Shepherd, Mausoleum of Galla Placidia, Ravenna |
| Type | monotheistic |
| Birth Place | Ulm, Kingdom of Württemberg, German Empire |
```

An infobox with no image simply begins with its first data field; no empty
`Image` or `Caption` rows are added.

Compound infoboxes are split by their own internal headings. For example:

```markdown
| Attribute | Value |
| --- | --- |
| Image | ![Portrait](https://assets.grokipedia.com/wiki/images/example.jpg) |
| Caption | Official portrait |

### First Office

| Attribute | Value |
| --- | --- |
| Term | 2000–2005 |
| Predecessor | Person A |

### Second Office

| Attribute | Value |
| --- | --- |
| Term | 1995–2000 |
| Successor | Person B |
```

Article figures are emitted in reading order like this:

```markdown
![Crowd assembled in the Hall of Mirrors at the Palace of Versailles](https://assets.grokipedia.com/wiki/images/2be895eec1e0.jpg)

*Caption:* The Hall of Mirrors during the signing ceremony of the Treaty of Versailles
```

Network fetching is done on a worker thread, so the window stays responsive while a live page is being downloaded.

## Command line

### Use a live Grokipedia URL

```bash
./grokipedia-to-markdown \
  "https://grokipedia.com/page/Ludwig_von_Mises" \
  -o ludwig-von-mises.md
```

### Use a saved HTML page

```bash
./grokipedia-to-markdown \
  "Ludwig von Mises — Grokipedia.html" \
  -o ludwig-von-mises.md
```

If `-o` is omitted, Markdown is printed to standard output.

Citations such as `[1][2]` in Grokipedia become `[^1][^2]`, with definitions such as:

```markdown
[^1]: [Ludwig von Mises](https://mises.org/profile/ludwig-von-mises)
[^2]: [Ludwig von Mises | Online Library of Liberty](https://oll.libertyfund.org/people/ludwig-von-mises)
```
