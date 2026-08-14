# Grokipedia to Markdown

A small Python program that converts a Grokipedia article into sensible Markdown and turns Grokipedia's numbered citations into Markdown footnotes.

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
