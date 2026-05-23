"""Markdown → PDF via Edge headless (Windows 11 built-in). No external deps."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Force UTF-8 on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from md2html import convert_file


def find_edge() -> str:
    """Locate Microsoft Edge executable."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            return c

    # Try to find via 'where'
    result = shutil.which("msedge")
    if result:
        return result

    raise FileNotFoundError("Microsoft Edge not found. Install Edge or set EDGE_PATH env var.")


def html_to_pdf(html_path: str, pdf_path: str, edge_path: str | None = None) -> str:
    """Convert HTML file to PDF using Edge headless mode."""
    html_file = Path(html_path)
    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    pdf_file = Path(pdf_path)
    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    # Edge requires absolute file:// URL
    html_url = html_file.resolve().as_uri()

    edge = edge_path or find_edge()
    cmd = [
        edge,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={pdf_file.resolve()}",
        "--no-pdf-header-footer",
        html_url,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        timeout=60,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        stderr_msg = result.stderr or "(no stderr)"
        raise RuntimeError(f"Edge PDF conversion failed (rc={result.returncode}):\n{stderr_msg}")

    return str(pdf_file.resolve())


def convert(md_path: str, pdf_path: str | None = None, edge_path: str | None = None) -> str:
    """Convert Markdown file to PDF. Returns the PDF path."""
    md_file = Path(md_path)
    if not md_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    if pdf_path is None:
        pdf_path = str(md_file.with_suffix(".pdf"))

    # Step 1: MD → HTML (temp file)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, encoding="utf-8", mode="w") as f:
        html_temp = f.name

    try:
        convert_file(md_path, html_temp, title=md_file.stem)
        # Step 2: HTML → PDF
        return html_to_pdf(html_temp, pdf_path, edge_path)
    finally:
        Path(html_temp).unlink(missing_ok=True)


def convert_dir(md_dir: str, pdf_dir: str | None = None, edge_path: str | None = None) -> list[str]:
    """Convert all .md files in a directory to PDF."""
    src = Path(md_dir)
    if not src.is_dir():
        raise NotADirectoryError(f"Not a directory: {md_dir}")

    if pdf_dir is None:
        pdf_dir = str(src)

    results = []
    for md_file in sorted(src.glob("*.md")):
        pdf_file = str(Path(pdf_dir) / md_file.with_suffix(".pdf").name)
        result = convert(str(md_file), pdf_file, edge_path)
        results.append(result)
        print(f"  ✓ {md_file.name} → {Path(result).name}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python md2pdf.py <input.md> [output.pdf]")
        print("       python md2pdf.py --dir <directory>  (convert all .md in dir)")
        sys.exit(1)

    if sys.argv[1] == "--dir":
        if len(sys.argv) < 3:
            print("Usage: python md2pdf.py --dir <directory> [output_dir]")
            sys.exit(1)
        src_dir = sys.argv[2]
        out_dir = sys.argv[3] if len(sys.argv) > 3 else None
        print(f"Converting all .md files in: {src_dir}")
        results = convert_dir(src_dir, out_dir)
        print(f"\nDone: {len(results)} files converted.")
    else:
        md_path = sys.argv[1]
        pdf_path = sys.argv[2] if len(sys.argv) > 2 else None
        result = convert(md_path, pdf_path)
        print(f"PDF written to: {result}")
