import hashlib
from pathlib import Path

import click


@click.group()
def evidence_group():
    """Evidence management — verify integrity and clean up orphaned references."""
    pass


@evidence_group.command()
@click.argument("case_id")
def verify(case_id: str):
    """Verify evidence integrity for a case. Scans evidence files and checks SHA256."""
    evidence_dir = Path("shared") / "cases" / case_id / "evidence"
    if not evidence_dir.exists():
        click.echo(f"No evidence directory for case '{case_id}'.")
        return

    files = [f for f in evidence_dir.rglob("*") if f.is_file()]
    if not files:
        click.echo(f"No evidence files for case '{case_id}'.")
        return

    ok = 0
    mismatch = 0
    for f in sorted(files):
        rel = f.relative_to(evidence_dir)
        actual_hash = hashlib.sha256(f.read_bytes()).hexdigest()
        # Check if hash file exists
        hash_file = f.with_suffix(f.suffix + ".sha256")
        if hash_file.exists():
            expected = hash_file.read_text(encoding="utf-8").strip().split()[0]
            if actual_hash == expected:
                ok += 1
                click.echo(f"  OK: {rel}")
            else:
                mismatch += 1
                click.echo(f"  MISMATCH: {rel} (expected {expected[:16]}..., got {actual_hash[:16]}...)")
        else:
            # No hash file yet — compute and store
            hash_file.write_text(f"{actual_hash}  {f.name}", encoding="utf-8")
            click.echo(f"  INDEXED: {rel} (new)")

    click.echo(f"\n{ok} OK, {mismatch} mismatch, {len(files)} total")
    if mismatch:
        click.echo("CRITICAL: Hash mismatches detected! Evidence may be tampered.")


@evidence_group.command()
@click.argument("case_id")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def purge_orphans(case_id: str, yes: bool):
    """Remove orphaned evidence index entries (hash files without evidence)."""
    evidence_dir = Path("shared") / "cases" / case_id / "evidence"
    if not evidence_dir.exists():
        click.echo(f"No evidence directory for case '{case_id}'.")
        return

    # Find .sha256 files whose evidence file is missing
    orphans = []
    for hf in evidence_dir.rglob("*.sha256"):
        evidence_file = hf.with_suffix("")
        if not evidence_file.exists():
            orphans.append(hf)

    if not orphans:
        click.echo("No orphaned index entries found.")
        return

    click.echo(f"Found {len(orphans)} orphaned hash file(s):")
    for o in orphans:
        click.echo(f"  {o.relative_to(evidence_dir)}")

    if not yes:
        click.confirm("\nDelete these orphaned entries?", abort=True)

    for o in orphans:
        o.unlink()
    click.echo(f"Purged {len(orphans)} orphaned entries.")
