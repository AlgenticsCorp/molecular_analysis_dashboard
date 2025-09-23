#!/usr/bin/env python3
"""Database migration runner."""

import asyncio
import os
import sys
import subprocess
import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command()
@click.option('--branch', default='metadata', help='Migration branch (metadata/results)')
@click.option('--upgrade', is_flag=True, help='Upgrade to latest migration')
@click.option('--downgrade', default=None, help='Downgrade to specific revision')
@click.option('--current', is_flag=True, help='Show current migration version')
@click.option('--history', is_flag=True, help='Show migration history')
@click.option('--org-id', default=None, help='Organization ID for results database')
def main(branch, upgrade, downgrade, current, history, org_id):
    """Database migration management."""

    # Set environment variables
    os.environ['ALEMBIC_BRANCH'] = branch

    # Adjust database URL for results database
    if branch == 'results' and org_id:
        base_url = os.getenv('DATABASE_URL')
        if base_url:
            # Replace database name with org-specific results database
            base_db = os.getenv('POSTGRES_DB', 'mad')
            results_url = base_url.replace(f'/{base_db}', f'/{base_db}_results_{org_id}')
            os.environ['DATABASE_URL'] = results_url

    try:
        if current:
            show_current_version(branch)
        elif history:
            show_migration_history(branch)
        elif upgrade:
            run_upgrade(branch)
        elif downgrade:
            run_downgrade(branch, downgrade)
        else:
            console.print("No action specified. Use --help for options.", style="yellow")

    except Exception as e:
        console.print(f"Migration failed: {e}", style="red")
        sys.exit(1)


def show_current_version(branch):
    """Show current migration version."""
    console.print(f"Current migration version for [bold]{branch}[/bold] branch:")

    result = subprocess.run(
        ['alembic', '-c', 'alembic.ini', 'current'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        console.print(result.stdout.strip() or "No migrations applied", style="green")
    else:
        console.print(f"Error: {result.stderr}", style="red")


def show_migration_history(branch):
    """Show migration history."""
    console.print(f"Migration history for [bold]{branch}[/bold] branch:")

    result = subprocess.run(
        ['alembic', '-c', 'alembic.ini', 'history', '--verbose'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        console.print(result.stdout)
    else:
        console.print(f"Error: {result.stderr}", style="red")


def run_upgrade(branch):
    """Run database upgrade."""
    console.print(f"Upgrading [bold]{branch}[/bold] database to latest version...")

    # Check database connectivity first
    if not check_database_connectivity():
        console.print("Database connection failed. Please check your connection settings.", style="red")
        sys.exit(1)

    result = subprocess.run(
        ['alembic', '-c', 'alembic.ini', 'upgrade', 'head'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        console.print("✅ Database upgrade completed successfully!", style="green")
        if result.stdout:
            console.print(result.stdout)
    else:
        console.print(f"❌ Migration failed: {result.stderr}", style="red")
        sys.exit(1)


def run_downgrade(branch, revision):
    """Run database downgrade."""
    console.print(f"Downgrading [bold]{branch}[/bold] database to revision: {revision}")

    result = subprocess.run(
        ['alembic', '-c', 'alembic.ini', 'downgrade', revision],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        console.print("✅ Database downgrade completed successfully!", style="green")
        if result.stdout:
            console.print(result.stdout)
    else:
        console.print(f"❌ Downgrade failed: {result.stderr}", style="red")
        sys.exit(1)


def check_database_connectivity():
    """Check if database is accessible."""
    try:
        import asyncpg
        import asyncio

        async def test_connection():
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                return False

            try:
                # Convert to asyncpg format if needed
                if database_url.startswith('postgresql+asyncpg://'):
                    database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

                conn = await asyncpg.connect(database_url)
                await conn.execute('SELECT 1')
                await conn.close()
                return True
            except Exception:
                return False

        return asyncio.run(test_connection())
    except ImportError:
        console.print("Warning: asyncpg not available, skipping connectivity check", style="yellow")
        return True


if __name__ == '__main__':
    main()
