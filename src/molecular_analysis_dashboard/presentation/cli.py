"""Command-line interface for Molecular Analysis Dashboard."""

from __future__ import annotations

import sys

import click


@click.group()
def main() -> None:  # pragma: no cover - thin wrapper
    """Molecular Analysis Dashboard CLI."""
    pass


@main.command()
def version() -> None:
    """Print version and exit."""
    from molecular_analysis_dashboard import __version__  # noqa: PLC0415

    click.echo(__version__)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
