"""This module defines CLI commands for the PipePal application."""

import click
import asyncio
import json
import logging
from .app import process_input_extract_rationale

logger = logging.getLogger(__name__)

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
        "The terms for which support or rationale should be sought. Can be a single term or multiple terms separated by commas (e.g., 'Astrocyte' or 'Astrocyte,Ependymal')"
    )
)
def extract_evidence(config, source, terms):
    try:
        # Parse terms - handle both single terms and JSON arrays
        try:
            # First try to parse as JSON
            try:
                parsed_terms = json.loads(terms)
                if isinstance(parsed_terms, list):
                    if not all(isinstance(t, str) for t in parsed_terms):
                        raise ValueError("All terms must be strings")
                else:
                    raise ValueError("JSON input must be an array")
            except json.JSONDecodeError:
                # If JSON parsing fails, try to split by comma
                if ',' in terms:
                    # Split by comma and clean up each term
                    parsed_terms = [t.strip(' "[]\'') for t in terms.split(',')]
                else:
                    # Single term - clean up any quotes or brackets
                    parsed_terms = terms.strip(' "[]\'')
            
            logger.info(f"Parsed terms: {parsed_terms}")
            
        except Exception as e:
            click.echo(f"Error parsing terms: {str(e)}", err=True)
            click.echo("Terms should be either a single term or multiple terms separated by commas", err=True)
            click.echo("Example: --terms \"Astrocyte\" or --terms \"Astrocyte,Ependymal\"", err=True)
            raise click.Abort()

        # Run the async function using asyncio.run()
        result = asyncio.run(process_input_extract_rationale(
            config=config,
            source=source,
            terms=parsed_terms
        ))
        
        if result.get("status") == "Error":
            click.echo(f"Error: {result.get('error')}", err=True)
            raise click.Abort()
            
        # Display results in a structured format
        click.echo("\nProcessing Results:")
        click.echo(f"File: {result.get('file')}")
        click.echo(f"Status: {result.get('status')}")
        
        if result.get('results'):
            click.echo("\nLLM Results:")
            for model, response in result['results'].items():
                click.echo(f"\n=== {model} ===")
                try:
                    # Try to parse and format JSON response
                    if isinstance(response, str):
                        try:
                            parsed_response = json.loads(response)
                            response = json.dumps(parsed_response, indent=2)
                        except json.JSONDecodeError:
                            pass
                    
                    # Print the response
                    click.echo(response)
                except Exception as e:
                    click.echo(f"Error formatting response: {str(e)}")
                    click.echo(response)
        
        if result.get('metadata'):
            click.echo("\nDocument Metadata:")
            for key, value in result['metadata'].items():
                click.echo(f"{key}: {value}")
                
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == "__main__":
    cli()
