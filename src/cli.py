"""Command-line interface"""

import click
import sys
import logging


@click.command()
@click.option(
    '--start-date',
    required=True,
    type=str,
    help='Start date (YYYY-MM-DD)'
)
@click.option(
    '--end-date',
    required=True,
    type=str,
    help='End date (YYYY-MM-DD)'
)
@click.option(
    '--users',
    required=False,
    type=str,
    default=None,
    help='Comma-separated user emails (optional, defaults to all users in workspace)'
)
@click.option(
    '--use-cache',
    is_flag=True,
    default=False,
    help='Use cached data instead of fetching from Toggl'
)
@click.option(
    '--config',
    type=click.Path(exists=True),
    default='config/config.yaml',
    help='Path to config file'
)
@click.option(
    '--output-dir',
    type=click.Path(),
    default='./tmp',
    help='Output directory'
)
@click.option(
    '--log-level',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
    default='INFO',
    help='Logging level'
)
def main(start_date, end_date, users, use_cache, config, output_dir, log_level):
    """Generate team activity reports from Toggl time tracking data.
    
    Examples:
    
    # Generate report for all users
    python generate_report.py --start-date 2025-09-23 --end-date 2025-09-29
    
    # Generate report for specific users
    python generate_report.py --start-date 2025-09-23 --end-date 2025-09-29 --users user1@example.com,user2@example.com
    
    # Use cached data (development mode)
    python generate_report.py --start-date 2025-09-23 --end-date 2025-09-29 --use-cache
    """
    from .main import run_report_generation
    
    # Parse user emails (None means all users)
    user_emails = None if users is None else [email.strip() for email in users.split(',')]
    
    # Run the report generation
    try:
        run_report_generation(
            start_date=start_date,
            end_date=end_date,
            user_emails=user_emails,
            use_cache=use_cache,
            config_path=config,
            output_dir=output_dir,
            log_level=log_level
        )
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

