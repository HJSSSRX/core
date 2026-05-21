import asyncio

from forhacker.meta.browser import WebBrowser
from forhacker.meta.sources import Source


def test_browser_extract_preview():
    html = "<html><head><title>Test Page</title></head><body><p>Hello World</p></body></html>"
    title, snippet = WebBrowser._extract_preview(html)
    assert title == "Test Page"
    assert "Hello World" in snippet


def test_browser_extract_no_title():
    html = "<html><body>Content here</body></html>"
    title, snippet = WebBrowser._extract_preview(html)
    assert title == ""
    assert "Content here" in snippet


def test_browser_fetch_invalid_url():
    browser = WebBrowser()
    source = Source(name="bad", url="http://localhost:1/nonexistent", category="test")
    result = asyncio.run(browser.fetch_source(source))
    assert result.status in ("error", "timeout")


def test_browser_scan_all_empty():
    browser = WebBrowser()
    results = asyncio.run(browser.scan_all([]))
    assert results == []
