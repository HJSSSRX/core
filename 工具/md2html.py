"""Markdown to styled HTML converter — stdlib only, print-friendly output."""

from __future__ import annotations

import html as html_mod
import re
from pathlib import Path

CSS = """
:root {
  --bg: #ffffff; --text: #1a1a1a; --muted: #666666; --accent: #1a6fb5;
  --border: #dddddd; --code-bg: #f5f5f5; --table-stripe: #f9f9f9;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Microsoft YaHei", "SimHei", sans-serif;
  line-height: 1.8; color: var(--text); max-width: 800px;
  margin: 2rem auto; padding: 0 1.5rem;
}
h1 { font-size: 1.6rem; color: var(--accent); border-bottom: 2px solid var(--accent);
     padding-bottom: 0.4rem; margin: 2rem 0 1rem; }
h2 { font-size: 1.3rem; color: var(--accent); margin: 1.8rem 0 0.8rem;
     padding-left: 0.6rem; border-left: 4px solid var(--accent); }
h3 { font-size: 1.1rem; margin: 1.2rem 0 0.5rem; }
p { margin: 0.6rem 0; }
strong { color: #000; }
code {
  background: var(--code-bg); padding: 0.15rem 0.4rem; border-radius: 3px;
  font-family: "Cascadia Code", "Consolas", monospace; font-size: 0.9rem;
}
pre {
  background: var(--code-bg); padding: 1rem 1.2rem; border-radius: 6px;
  overflow-x: auto; margin: 0.8rem 0; border: 1px solid var(--border);
  font-family: "Cascadia Code", "Consolas", monospace; font-size: 0.85rem; line-height: 1.5;
}
pre code { background: none; padding: 0; font-size: inherit; }
blockquote {
  border-left: 3px solid var(--accent); padding: 0.5rem 1rem; margin: 0.8rem 0;
  background: #f0f6fb; color: #444;
}
ul, ol { margin: 0.5rem 0 0.5rem 1.8rem; }
li { margin: 0.2rem 0; }
table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
th, td { padding: 0.5rem 0.8rem; text-align: left; border: 1px solid var(--border); font-size: 0.9rem; }
th { background: #e8f0f8; color: var(--accent); font-weight: 600; }
tr:nth-child(even) td { background: var(--table-stripe); }
hr { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
@media print {
  body { max-width: 100%; margin: 0; padding: 0.5rem; font-size: 12pt; }
  h1 { font-size: 18pt; } h2 { font-size: 15pt; } h3 { font-size: 13pt; }
  pre, code { font-size: 9pt; }
  @page { margin: 1.5cm; }
}
"""


def convert(md_text: str, title: str = "") -> str:
    """Convert Markdown text to a full styled HTML page."""
    lines = md_text.split("\n")
    html_lines = []
    i = 0
    in_code_block = False
    code_content: list[str] = []
    in_table = False
    table_rows: list[str] = []
    in_list = False
    list_tag = ""

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            return
        html_lines.append("<table>")
        for idx, row in enumerate(table_rows):
            cells = [c.strip() for c in row.split("|") if c.strip() != ""]
            tag = "th" if idx == 0 else "td"
            html_lines.append("<tr>")
            for cell in cells:
                html_lines.append(f"<{tag}>{cell.strip()}</{tag}>")
            html_lines.append("</tr>")
        html_lines.append("</table>")
        table_rows = []
        in_table = False

    def flush_list():
        nonlocal in_list, list_tag
        if in_list:
            html_lines.append(f"</{list_tag}>")
            in_list = False
            list_tag = ""

    def inline_format(text: str) -> str:
        text = html_mod.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = re.sub(r"_(.+?)_", r"<em>\1</em>", text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
        return text

    while i < len(lines):
        line = lines[i]

        # Code block toggle
        if line.strip().startswith("```"):
            if in_code_block:
                escaped = html_mod.escape("\n".join(code_content))
                html_lines.append(f"<pre>{escaped}</pre>")
                code_content = []
                in_code_block = False
            else:
                flush_list()
                flush_table()
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_content.append(line)
            i += 1
            continue

        # Table
        if "|" in line and line.strip().startswith("|"):
            flush_list()
            if not in_table:
                in_table = True
                table_rows = []
            # Skip separator rows like |---|---|
            if re.match(r"^\|[\s\-:|]+\|$", line.strip()):
                i += 1
                continue
            table_rows.append(line.strip())
            i += 1
            continue
        else:
            if in_table:
                flush_table()

        # Blank line — flush list
        if line.strip() == "":
            flush_list()
            html_lines.append("")
            i += 1
            continue

        # Heading
        h_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if h_match:
            flush_list()
            level = len(h_match.group(1))
            text = inline_format(h_match.group(2))
            html_lines.append(f"<h{level}>{text}</h{level}>")
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^[-*_]{3,}\s*$", line.strip()):
            flush_list()
            html_lines.append("<hr>")
            i += 1
            continue

        # Blockquote
        if line.strip().startswith("> "):
            flush_list()
            text = inline_format(line.strip()[2:])
            html_lines.append(f"<blockquote>{text}</blockquote>")
            i += 1
            continue

        # Unordered list
        ul_match = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
        if ul_match:
            if not in_list or list_tag != "ul":
                flush_list()
                html_lines.append("<ul>")
                in_list = True
                list_tag = "ul"
            html_lines.append(f"<li>{inline_format(ul_match.group(2))}</li>")
            i += 1
            continue

        # Ordered list
        ol_match = re.match(r"^(\s*)\d+[.)]\s+(.+)$", line)
        if ol_match:
            if not in_list or list_tag != "ol":
                flush_list()
                html_lines.append("<ol>")
                in_list = True
                list_tag = "ol"
            html_lines.append(f"<li>{inline_format(ol_match.group(2))}</li>")
            i += 1
            continue

        # Paragraph
        flush_list()
        html_lines.append(f"<p>{inline_format(line.strip())}</p>")
        i += 1

    # Flush trailing state
    flush_list()
    flush_table()

    body = "\n".join(html_lines)
    page_title = title or "Document"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_mod.escape(page_title)}</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def convert_file(md_path: str, html_path: str | None = None, title: str = "") -> str:
    """Convert a Markdown file to HTML. Returns the HTML path."""
    md_file = Path(md_path)
    if not md_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    if html_path is None:
        html_path = str(md_file.with_suffix(".html"))

    md_text = md_file.read_text(encoding="utf-8")
    if not title:
        title = md_file.stem

    html = convert(md_text, title)
    Path(html_path).write_text(html, encoding="utf-8")
    return html_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python md2html.py <input.md> [output.html]")
        sys.exit(1)

    md_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    result = convert_file(md_path, out_path)
    print(f"HTML written to: {result}")
