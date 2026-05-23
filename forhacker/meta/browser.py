import asyncio
import logging
from dataclasses import dataclass

from forhacker.meta.sources import Source

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 30.0


@dataclass
class ScrapeResult:
    source: str
    url: str
    title: str
    snippet: str
    status: str  # ok | timeout | error
    error: str | None = None


class WebBrowser:
    """Fetches content from MetaAgent sources using httpx."""

    async def fetch_source(self, source: Source) -> ScrapeResult:
        try:
            import httpx
        except ImportError:
            return ScrapeResult(
                source=source.name,
                url=source.url,
                title="",
                snippet="",
                status="error",
                error="httpx not installed",
            )

        try:
            async with httpx.AsyncClient(timeout=FETCH_TIMEOUT) as client:
                resp = await client.get(source.url, follow_redirects=True)
                resp.raise_for_status()
                title, snippet = self._extract_preview(resp.text)
                return ScrapeResult(
                    source=source.name,
                    url=source.url,
                    title=title,
                    snippet=snippet,
                    status="ok",
                )
        except httpx.TimeoutException:
            return ScrapeResult(
                source=source.name,
                url=source.url,
                title="",
                snippet="",
                status="timeout",
                error=f"Timed out after {FETCH_TIMEOUT}s",
            )
        except Exception as exc:
            return ScrapeResult(
                source=source.name,
                url=source.url,
                title="",
                snippet="",
                status="error",
                error=str(exc),
            )

    @staticmethod
    def _extract_preview(html: str) -> tuple[str, str]:
        title = ""
        snippet = ""
        if "<title>" in html:
            start = html.index("<title>") + 7
            end = html.index("</title>", start)
            title = html[start:end].strip()[:200]
        # Crude text extraction: strip tags
        text = ""
        in_tag = False
        for ch in html:
            if ch == "<":
                in_tag = True
            elif ch == ">":
                in_tag = False
            elif not in_tag:
                text += ch
        snippet = " ".join(text.split())[:500]
        return title, snippet

    async def scan_all(self, sources: list[Source], max_concurrency: int = 3) -> list[ScrapeResult]:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def fetch_one(source: Source) -> ScrapeResult:
            async with semaphore:
                return await self.fetch_source(source)

        tasks = [fetch_one(s) for s in sources]
        return list(await asyncio.gather(*tasks))
