"""MetaAgent scheduler — periodic scan→evaluate→propose→audit→introspect loop."""

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forhacker.meta.agent import MetaAgent
from forhacker.meta.evaluator import Proposal

logger = logging.getLogger(__name__)

SCAN_INTERVAL_HOURS = 6


class MetaScheduler:
    """Runs the MetaAgent loop: fetch sources → evaluate → file proposals → introspect → record audit trail."""

    def __init__(self, kb_dir: Path, proposals_dir: Path):
        self._agent = MetaAgent()
        self._kb_dir = kb_dir
        self._proposals_dir = proposals_dir
        self._proposals_dir.mkdir(parents=True, exist_ok=True)
        self._last_scan: dict[str, str] = {}

    async def scan_once(self) -> dict[str, Any]:
        from forhacker.meta.browser import WebBrowser
        from forhacker.meta.introspection import IntrospectionAgent

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

        # Run Platform Optimizer introspection
        introspector = IntrospectionAgent()
        code_issues = introspector.scan()
        plugin_info = introspector.list_registered_plugins()
        metrics = introspector.get_recent_metrics()

        if code_issues:
            issues_summary = "\n".join(
                f"- [{i.severity}] {i.file}:{i.line} — {i.description}"
                for i in code_issues[:10]
            )
            opt_proposal = Proposal(
                title="[Platform Optimizer] Code quality issues detected",
                what=f"Introspection found {len(code_issues)} potential issues:\n{issues_summary}",
                why="Automated code quality scan via AST analysis",
                impact="Code quality",
                risk="LOW",
                requires_coordination=False,
                relevance_score=0.6,
                quality_score=0.5,
            )
            if self._agent.submit_proposal(opt_proposal):
                passed += 1
                self._save_proposal(opt_proposal)

        # Report platform state
        logger.info("Platform state: %d plugins, %d KB entries, %d test files",
                     len(plugin_info), metrics.get("kb_entry_count", 0), metrics.get("test_count", 0))

        self._agent.evaluator.record_day(candidates=candidates, passed=passed)
        self._last_scan["timestamp"] = datetime.now(timezone.utc).isoformat()

        if self._agent.evaluator.should_alert():
            logger.warning("MetaAgent watchdog: %d days with zero passed proposals", 7)

        return {
            "sources_checked": len(results),
            "candidates": candidates,
            "passed": passed,
            "pending_proposals": len(self._agent.list_pending()),
            "introspection_issues": len(code_issues),
            "plugins_registered": len(plugin_info),
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

    def create_snapshot(self, change_id: str, target_dirs: list[Path] | None = None) -> Path:
        """Create a backup snapshot of specified directories before applying a change.

        Returns the snapshot directory path.
        """
        snapshot_dir = self._proposals_dir / ".snapshots" / change_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        if target_dirs is None:
            target_dirs = [self._kb_dir] if self._kb_dir.exists() else []

        for d in target_dirs:
            if not d.exists():
                continue
            dest = snapshot_dir / d.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(d, dest)

        meta = {
            "change_id": change_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target_dirs": [str(d) for d in target_dirs],
        }
        import yaml
        (snapshot_dir / "snapshot_meta.yaml").write_text(
            yaml.dump(meta, allow_unicode=True), encoding="utf-8",
        )

        logger.info("Snapshot created: %s (%d dirs)", change_id, len(target_dirs))
        return snapshot_dir

    def restore_snapshot(self, change_id: str) -> dict[str, Any]:
        """Restore files from a backup snapshot. Returns result dict."""
        snapshot_dir = self._proposals_dir / ".snapshots" / change_id
        if not snapshot_dir.exists():
            return {"status": "error", "message": f"No snapshot found for change '{change_id}'"}

        import yaml
        meta_path = snapshot_dir / "snapshot_meta.yaml"
        meta: dict[str, Any] = {}
        if meta_path.exists():
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}

        restored = []
        failed = []
        for item in snapshot_dir.iterdir():
            if item.name == "snapshot_meta.yaml":
                continue
            target = item.resolve() if item.is_symlink() else None
            if target is None:
                target = Path(str(item)).parent.parent.parent / item.name
                # Map back: .snapshots/<id>/kb → <kb_dir location>
                # The target was stored in meta
                for td in meta.get("target_dirs", []):
                    if Path(td).name == item.name:
                        target = Path(td)
                        break
            try:
                if item.is_dir():
                    if Path(target).exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
                restored.append(str(item.name))
            except OSError as e:
                failed.append({"path": str(item.name), "error": str(e)})

        status = "ok" if not failed else "partial"
        result: dict[str, Any] = {
            "status": status,
            "change_id": change_id,
            "restored": restored,
            "failed": failed,
            "snapshot_meta": meta,
        }
        if failed:
            result["message"] = f"Restored {len(restored)} items, {len(failed)} failures"
        else:
            result["message"] = f"Restored {len(restored)} items from snapshot"
        return result

    def list_snapshots(self) -> list[dict[str, Any]]:
        """List all backup snapshots."""
        snapshots_dir = self._proposals_dir / ".snapshots"
        if not snapshots_dir.exists():
            return []
        import yaml
        results = []
        for d in sorted(snapshots_dir.iterdir()):
            if d.is_dir():
                meta: dict[str, Any] = {}
                meta_path = d / "snapshot_meta.yaml"
                if meta_path.exists():
                    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
                results.append({
                    "change_id": d.name,
                    "created_at": meta.get("created_at", "unknown"),
                    "target_dirs": meta.get("target_dirs", []),
                })
        return results
