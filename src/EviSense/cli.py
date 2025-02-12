"""This module defines CLI commands for the PipePal application."""

import click
import asyncio
from .app import process_input_extract_rationale

@click.group()
@click.pass_context
def cli(ctx):
    """CLI commands for the EviSense application"""
    pass


@cli.command()
@click.option(
    '--config',
    required=True,
    type=str,
    help=(
        "Path to the YAML config file or a JSON dictionary string."
    )
)

@click.option(
    '--source',
    required=True,
    help=(
        "The source—whether a file (text or PDF), a folder, or a text string—where evidence or rationale for the given term is searched."
    )
)

@click.option(
    '--terms',
    required=True,
    type=str,
    help=(
        "The terms for which support or rationale should be sought."
    )
)
def extract_evidence(config, source, terms):
    try:
        # Run the async function using asyncio.run()
        result = asyncio.run(process_input_extract_rationale(config=config, source=source, terms=terms))
        click.echo(result)
                
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == "__main__":
    cli()
