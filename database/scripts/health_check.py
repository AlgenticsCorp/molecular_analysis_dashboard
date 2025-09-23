#!/usr/bin/env python3
"""Database health check utility."""

import asyncio
import os
import sys
import time
from typing import Dict, Any
import click
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()


@click.command()
@click.option('--continuous', is_flag=True, help='Run continuous health monitoring')
@click.option('--interval', default=30, help='Check interval in seconds for continuous mode')
@click.option('--timeout', default=10, help='Connection timeout in seconds')
def main(continuous, interval, timeout):
    """Database health check utility."""

    if continuous:
        run_continuous_monitoring(interval, timeout)
    else:
        result = asyncio.run(run_single_check(timeout))
        if not result['overall_healthy']:
            sys.exit(1)


def run_continuous_monitoring(interval: int, timeout: int):
    """Run continuous health monitoring with live display."""
    console.print("🔍 Starting continuous database health monitoring...", style="blue")
    console.print(f"Check interval: {interval}s | Timeout: {timeout}s\n")

    try:
        while True:
            result = asyncio.run(run_single_check(timeout))
            display_health_status(result)

            if not result['overall_healthy']:
                console.print("⚠️  Health check failed - continuing monitoring...", style="yellow")

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n👋 Health monitoring stopped", style="blue")


async def run_single_check(timeout: int) -> Dict[str, Any]:
    """Run a single health check."""
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'checks': {},
        'overall_healthy': True
    }

    # Check metadata database
    results['checks']['metadata_db'] = await check_metadata_database(timeout)

    # Check Redis if configured
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        results['checks']['redis'] = await check_redis(redis_url, timeout)

    # Check if any organization results databases exist
    results['checks']['results_db'] = await check_results_databases(timeout)

    # Determine overall health
    results['overall_healthy'] = all(
        check.get('healthy', False) for check in results['checks'].values()
    )

    return results


async def check_metadata_database(timeout: int) -> Dict[str, Any]:
    """Check metadata database connectivity and basic operations."""
    result = {
        'healthy': False,
        'response_time_ms': 0,
        'error': None,
        'details': {}
    }

    try:
        import asyncpg

        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            result['error'] = 'DATABASE_URL not configured'
            return result

        # Convert URL format
        if database_url.startswith('postgresql+asyncpg://'):
            database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

        start_time = time.time()

        conn = await asyncio.wait_for(
            asyncpg.connect(database_url),
            timeout=timeout
        )

        # Test basic query
        version = await conn.fetchval('SELECT version()')

        # Check if our tables exist
        tables_count = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('organizations', 'users', 'task_definitions')
        """)

        await conn.close()

        result['response_time_ms'] = int((time.time() - start_time) * 1000)
        result['healthy'] = True
        result['details'] = {
            'postgres_version': version.split()[1] if version else 'unknown',
            'tables_count': tables_count
        }

    except asyncio.TimeoutError:
        result['error'] = f'Connection timeout after {timeout}s'
    except Exception as e:
        result['error'] = str(e)

    return result


async def check_redis(redis_url: str, timeout: int) -> Dict[str, Any]:
    """Check Redis connectivity."""
    result = {
        'healthy': False,
        'response_time_ms': 0,
        'error': None,
        'details': {}
    }

    try:
        import redis.asyncio as redis

        start_time = time.time()

        r = redis.from_url(redis_url)

        # Test basic operations
        await asyncio.wait_for(r.ping(), timeout=timeout)
        info = await r.info()

        await r.close()

        result['response_time_ms'] = int((time.time() - start_time) * 1000)
        result['healthy'] = True
        result['details'] = {
            'redis_version': info.get('redis_version', 'unknown'),
            'used_memory': info.get('used_memory_human', 'unknown'),
            'connected_clients': info.get('connected_clients', 0)
        }

    except asyncio.TimeoutError:
        result['error'] = f'Redis timeout after {timeout}s'
    except ImportError:
        result['error'] = 'Redis client not available'
    except Exception as e:
        result['error'] = str(e)

    return result


async def check_results_databases(timeout: int) -> Dict[str, Any]:
    """Check sample results database connectivity."""
    result = {
        'healthy': True,  # Default to healthy since results DBs are created on-demand
        'response_time_ms': 0,
        'error': None,
        'details': {
            'note': 'Results databases are created on-demand per organization',
            'template_db_configured': bool(os.getenv('RESULTS_DB_TEMPLATE'))
        }
    }

    # Could check template database or sample org database if available
    # For now, just verify the template URL is configured
    template_url = os.getenv('RESULTS_DB_TEMPLATE')
    if not template_url:
        result['healthy'] = False
        result['error'] = 'RESULTS_DB_TEMPLATE not configured'

    return result


def display_health_status(result: Dict[str, Any]):
    """Display health check results in a formatted table."""
    table = Table(title=f"Database Health Check - {result['timestamp']}")

    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Response Time", justify="right")
    table.add_column("Details")

    for component, check in result['checks'].items():
        status = "✅ Healthy" if check['healthy'] else "❌ Unhealthy"
        status_style = "green" if check['healthy'] else "red"

        response_time = f"{check['response_time_ms']}ms" if check['response_time_ms'] > 0 else "-"

        details = []
        if check.get('error'):
            details.append(f"Error: {check['error']}")

        if check.get('details'):
            for key, value in check['details'].items():
                details.append(f"{key}: {value}")

        table.add_row(
            component.replace('_', ' ').title(),
            f"[{status_style}]{status}[/{status_style}]",
            response_time,
            " | ".join(details)
        )

    # Overall status
    overall_status = "✅ All Systems Healthy" if result['overall_healthy'] else "❌ System Issues Detected"
    overall_style = "green" if result['overall_healthy'] else "red"

    console.print(table)
    console.print(f"\n[{overall_style}]{overall_status}[/{overall_style}]\n")


if __name__ == '__main__':
    main()
