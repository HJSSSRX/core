"""MetaAgent scheduler — periodic scan→evaluate→propose→audit loop."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forhacker.meta.agent import MetaAgent
from forhacker.meta.evaluator import Proposal

logger = logging.getLogger(__name__)

SCAN_INTERVAL_HOURS = 6


class MetaScheduler:
    """Runs the MetaAgent loop: fetch sources → evaluate → file proposals → record audit trail."""

    def __init__(self, kb_dir: Path, proposals_dir: Path):
        self._agent = MetaAgent()
        self._kb_dir = kb_dir
        self._proposals_dir = proposals_dir
        self._proposals_dir.mkdir(parents=True, exist_ok=True)
        self._last_scan: dict[str, str] = {}

    async def scan_once(self) -> dict[str, Any]:
        from forhacker.meta.browser import WebBrowser

        browser = WebBrowser()
        results = await browser.scan_all(self._agent.sources)
        candidates = 0
        passed = 0

        for r in results:
            if r.status != "ok" or not r.snippet:
                continue
            candidates += 1
            proposal = Proposal(
                title=f"[{r.source}] {r.title[:80]}",
                what=f"Potential improvement detected from {r.source}: {r.snippet[:200]}",
                why=f"Source URL: {r.url}",
                impact="To be evaluated",
                risk="LOW",
                requires_coordination=False,
                relevance_score=0.5,
                quality_score=0.5,
            )
            if self._agent.submit_proposal(proposal):
                passed += 1
                self._save_proposal(proposal)

        self._agent.evaluator.record_day(candidates=candidates, passed=passed)
        self._last_scan["timestamp"] = datetime.now(timezone.utc).isoformat()

        if self._agent.evaluator.should_alert():
            logger.warning("MetaAgent watchdog: %d days with zero passed proposals", 7)

        return {
            "sources_checked": len(results),
            "candidates": candidates,
            "passed": passed,
            "pending_proposals": len(self._agent.list_pending()),
        }

    def _save_proposal(self, proposal: Proposal) -> None:
        import yaml
        filename = f"{proposal.title[:40].replace(' ', '_').replace('/', '_')}.yaml"
        path = self._proposals_dir / filename
        data = {
            "title": proposal.title,
            "what": proposal.what,
            "why": proposal.why,
            "impact": proposal.impact,
            "risk": proposal.risk,
            "requires_coordination": proposal.requires_coordination,
            "relevance_score": proposal.relevance_score,
            "quality_score": proposal.quality_score,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")

    def list_pending_proposals(self) -> list[dict[str, Any]]:
        import yaml
        proposals = []
        for p in sorted(self._proposals_dir.glob("*.yaml")):
            proposals.append(yaml.safe_load(p.read_text(encoding="utf-8")))
        return proposals

    def add_source(self, name: str, url: str, category: str) -> None:
        self._agent.add_source(name=name, url=url, category=category)
