#!/usr/bin/env python3
"""Desktop GUI for Grokipedia to Markdown."""

from __future__ import annotations

import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import unquote, urlparse

from grokipedia_to_markdown import convert_html, read_source


APP_TITLE = "Grokipedia to Markdown"


def suggested_filename(source: str, markdown: str = "") -> str:
    """Return a sensible .md filename for a URL/file source or converted Markdown."""
    source = source.strip()
    name = ""

    if source:
        parsed = urlparse(source)
        if parsed.scheme in {"http", "https"}:
            name = unquote(parsed.path.rstrip("/").split("/")[-1])
        else:
            name = Path(source).stem

    if not name and markdown:
        first_line = markdown.lstrip().splitlines()[0] if markdown.strip() else ""
        if first_line.startswith("# "):
            name = first_line[2:].strip()

    name = name.replace("_", " ").strip() or "grokipedia-article"
    name = re.sub(r"[^\w\-. ]+", "", name, flags=re.UNICODE)
    name = re.sub(r"\s+", "-", name).strip("-.").lower()
    return f"{name or 'grokipedia-article'}.md"


class GrokipediaGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1000x720")
        self.minsize(720, 520)

        self.source_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Choose a saved Grokipedia HTML file or paste an article URL.")
        self._busy = False
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self, padding=(14, 14, 14, 8))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Source:").grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.source_entry = ttk.Entry(top, textvariable=self.source_var)
        self.source_entry.grid(row=0, column=1, sticky="ew")
        self.source_entry.bind("<Return>", lambda _event: self.convert())

        self.browse_button = ttk.Button(top, text="Browse…", command=self.browse)
        self.browse_button.grid(row=0, column=2, padx=(8, 0))

        self.convert_button = ttk.Button(top, text="Convert", command=self.convert)
        self.convert_button.grid(row=0, column=3, padx=(8, 0))

        editor_frame = ttk.Frame(self, padding=(14, 4, 14, 8))
        editor_frame.grid(row=1, column=0, sticky="nsew")
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(1, weight=1)

        ttk.Label(editor_frame, text="Markdown preview").grid(row=0, column=0, sticky="w", pady=(0, 6))

        text_frame = ttk.Frame(editor_frame)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        self.text = tk.Text(
            text_frame,
            wrap="word",
            undo=True,
            padx=12,
            pady=12,
            font=("TkFixedFont", 11),
        )
        self.text.grid(row=0, column=0, sticky="nsew")

        yscroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=yscroll.set)

        bottom = ttk.Frame(self, padding=(14, 4, 14, 14))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        ttk.Label(bottom, textvariable=self.status_var).grid(row=0, column=0, sticky="w")

        self.copy_button = ttk.Button(bottom, text="Copy Markdown", command=self.copy_markdown)
        self.copy_button.grid(row=0, column=1, padx=(8, 0))

        self.save_button = ttk.Button(bottom, text="Save As…", command=self.save_as)
        self.save_button.grid(row=0, column=2, padx=(8, 0))

        self.source_entry.focus_set()

    def browse(self) -> None:
        filename = filedialog.askopenfilename(
            title="Choose a saved Grokipedia page",
            filetypes=[
                ("HTML files", "*.html *.htm"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.source_var.set(filename)
            self.convert()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.convert_button.configure(state=state)
        self.browse_button.configure(state=state)
        self.source_entry.configure(state=state)
        if busy:
            self.status_var.set("Converting…")

    def convert(self) -> None:
        if self._busy:
            return

        source = self.source_var.get().strip()
        if not source:
            messagebox.showinfo(APP_TITLE, "Paste a Grokipedia URL or choose a saved HTML file first.")
            return

        self._set_busy(True)
        thread = threading.Thread(target=self._convert_worker, args=(source,), daemon=True)
        thread.start()

    def _convert_worker(self, source: str) -> None:
        try:
            html, fetched_url = read_source(source)
            markdown = convert_html(html, fetched_url)
        except Exception as exc:  # Keep Tk calls on the main thread.
            self.after(0, self._conversion_failed, str(exc))
        else:
            self.after(0, self._conversion_finished, markdown)

    def _conversion_finished(self, markdown: str) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", markdown)
        self.text.edit_modified(False)
        self._set_busy(False)

        lines = markdown.count("\n")
        self.status_var.set(f"Converted successfully — {lines:,} lines of Markdown.")

    def _conversion_failed(self, error: str) -> None:
        self._set_busy(False)
        self.status_var.set("Conversion failed.")
        messagebox.showerror(APP_TITLE, error)

    def _markdown(self) -> str:
        return self.text.get("1.0", "end-1c")

    def save_as(self) -> None:
        markdown = self._markdown()
        if not markdown.strip():
            messagebox.showinfo(APP_TITLE, "Convert an article before saving.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Markdown",
            defaultextension=".md",
            initialfile=suggested_filename(self.source_var.get(), markdown),
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
        )
        if not filename:
            return

        try:
            Path(filename).write_text(markdown.rstrip() + "\n", encoding="utf-8")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not save the file:\n\n{exc}")
            return

        self.status_var.set(f"Saved {Path(filename).name}")

    def copy_markdown(self) -> None:
        markdown = self._markdown()
        if not markdown.strip():
            messagebox.showinfo(APP_TITLE, "Convert an article before copying.")
            return

        self.clipboard_clear()
        self.clipboard_append(markdown)
        self.update_idletasks()
        self.status_var.set("Markdown copied to the clipboard.")


def main() -> int:
    app = GrokipediaGUI()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
