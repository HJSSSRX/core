from pathlib import Path

import click

from forhacker.cli.commands.plugin import _discover_plugins


@click.group()
def system_group():
    """System status and diagnostics."""
    pass


@system_group.command()
def status():
    """Show overall platform health — plugins, KB, cases, and project stats."""
    click.echo("=== ForHacker System Status ===\n")

    # Plugins
    try:
        manager = _discover_plugins()
        plugins = manager.loaded_plugins
        total_tools = sum(len(manager.get_plugin_tools(p)) for p in plugins)
        click.echo(f"[Plugins] {len(plugins)} loaded, {total_tools} tools")
        if manager.degraded_plugins:
            click.echo(f"  Degraded: {', '.join(manager.degraded_plugins)}")
        for name in sorted(plugins):
            tools = manager.get_plugin_tools(name)
            domains = {t.domain for t in tools}
            click.echo(f"  {name} ({len(tools)} tools, {', '.join(sorted(domains))})")
    except Exception as e:
        click.echo(f"[Plugins] ERROR: {e}")
    click.echo()

    # Knowledge Base
    kb_dir = Path("shared/kb")
    if kb_dir.exists():
        kb_files = list(kb_dir.glob("*.md"))
        click.echo(f"[Knowledge Base] {len(kb_files)} entries in shared/kb/")
    else:
        click.echo("[Knowledge Base] Not initialized (shared/kb/ missing)")
    click.echo()

    # Cases
    cases_dir = Path("shared/cases")
    if cases_dir.exists():
        case_dirs = [d for d in cases_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        click.echo(f"[Cases] {len(case_dirs)} case(s)")
        for cd in sorted(case_dirs):
            findings_files = list(cd.glob("**/*.md"))
            click.echo(f"  {cd.name} ({len(findings_files)} finding files)")
    else:
        click.echo("[Cases] No cases directory")
    click.echo()

    # Proposals
    proposals_dir = Path("shared/meta/proposals")
    if proposals_dir.exists():
        yaml_files = list(proposals_dir.glob("*.yaml"))
        click.echo(f"[MetaAgent] {len(yaml_files)} pending proposals")
        snapshots_dir = proposals_dir / ".snapshots"
        if snapshots_dir.exists():
            snaps = [d for d in snapshots_dir.iterdir() if d.is_dir()]
            click.echo(f"  {len(snaps)} snapshots available")
    else:
        click.echo("[MetaAgent] Not initialized")
    click.echo()

    # Evidence
    evidence_dir = Path("shared/evidence")
    if evidence_dir.exists():
        click.echo("[Evidence] shared/evidence/ present")
    else:
        click.echo("[Evidence] Not initialized")
    click.echo()

    # Project stats
    click.echo("[Project]")
    cells_count = len([d for d in Path("cells").iterdir() if d.is_dir() and not d.name.startswith(".")])
    click.echo(f"  Cell plugins: {cells_count}")
    tests_dir = Path("tests")
    if tests_dir.exists():
        test_files = list(tests_dir.rglob("test_*.py"))
        click.echo(f"  Test files: {len(test_files)}")


@system_group.command()
def env():
    """Show environment information for debugging."""
    import platform
    import sys

    click.echo(f"Python: {sys.version}")
    click.echo(f"Platform: {platform.platform()}")
    click.echo(f"cwd: {Path.cwd()}")

    # Check uv
    import shutil

    uv_path = shutil.which("uv")
    click.echo(f"uv: {uv_path or 'NOT FOUND'}")

    # Check git
    git_path = shutil.which("git")
    click.echo(f"git: {git_path or 'NOT FOUND'}")

    # Key directories
    for name in ["cells", "forhacker", "tests", "shared"]:
        d = Path(name)
        click.echo(f"{name}/: {'exists' if d.exists() else 'MISSING'}")
