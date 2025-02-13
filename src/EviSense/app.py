import yaml
import logging
import sys
from pathlib import Path
from typing import Union, Dict, List
from .shared import load_config, process_file, process_string_source

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def process_input_extract_rationale(config: Union[str, Path, Dict], source: Union[str, Path], terms: Union[str, List[str]]) -> dict:
    """
    Extracts rationale or evidence for a given term based on the provided configuration.

    Args:
        config (Union[str, Path, dict]): The configuration, which can be:
            - A YAML file path (`.yml` or `.yaml`).
            - A dictionary containing LLM configuration settings.
        source (Union[str, Path]): The source of information, which can be:
            - A string
            - A file path (pdf, text).
            - A directory path containing multiple files (text & pdf).
        terms (Union[str, List[str]]): Terms to extract rationale

    Returns:
        dict: A dictionary containing the extracted rationale or evidence for the given term.

    Raises:
        FileNotFoundError
        ValueError

    Example:
        >>> config_path = "config.yml"
        >>> source_directory = "documents/"
        >>> result = process_input_extract_rationale(config_path, source_path)
        >>> print(result)
    """
    try:
        # Load and validate config
        try:
            config_data = load_config(config)
            if not isinstance(config_data, dict):
                raise ValueError(f"Invalid configuration format: {type(config_data)}")
            if "llm" not in config_data:
                raise ValueError("Configuration must contain 'llm' section")
        except Exception as e:
            logger.error(f"Configuration error: {str(e)}")
            return {
                "status": "Error",
                "error": f"Configuration error: {str(e)}"
            }

        # Handle string source
        if isinstance(source, str) and not Path(source).exists():
            logger.info("Processing string source")
            return process_string_source(source, config_data)

        # Convert to Path and validate
        source_path = Path(source) if isinstance(source, str) else source
        if not source_path.exists():
            error_msg = f"Source path does not exist: {source}"
            logger.error(error_msg)
            return {
                "status": "Error",
                "error": error_msg
            }

        # Process single file
        if source_path.is_file():
            logger.info(f"Processing single file: {source_path}")
            return await process_file(
                file_path=source_path,
                config_data=config_data,
                terms=terms
            )

        # Process directory
        elif source_path.is_dir():
            logger.info(f"Processing directory: {source_path}")
            results = {}
            valid_extensions = {".txt", ".pdf"}
            
            for file_path in source_path.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
                    logger.info(f"Processing file: {file_path}")
                    results[file_path.name] = await process_file(
                        file_path=file_path,
                        config_data=config_data,
                        terms=terms
                    )
            
            if not results:
                return {
                    "status": "Error",
                    "error": f"No valid files found in directory: {source_path}"
                }
            
            return {
                "status": "Processed",
                "results": results
            }

        else:
            error_msg = f"Invalid source type: {source_path}"
            logger.error(error_msg)
            return {
                "status": "Error",
                "error": error_msg
            }

    except Exception as e:
        error_msg = f"Error in process_input_extract_rationale: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "Error",
            "error": error_msg
        }
