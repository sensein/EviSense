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


async def process_input_extract_rationale(config: Union[str, Path, Dict], source: Union[str, Path], terms:Union[str, List[str]]) -> dict:
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

    config_data = load_config(config)

    if isinstance(source, str):
        if not (Path(source).exists()):
            logger.info(f"Source is a string")
            return f"Source is string with config file {config_data}"

    # Convert to Path objects if they're strings
    source_path = Path(source) if isinstance(source, str) else source
    if not source_path.exists():
        logger.error(f"Source path does not exist: {source}")
        raise FileNotFoundError(f"Source path does not exist: {source}")

    if source_path.is_file():
        logger.info(f"Process single source file: {source_path}.")
        result = await process_file(file_path=source_path, config_data=config, terms=terms)
        if result["status"] == "Error":
            logger.error(f"Error processing file: {result['error']}")
            return result
        
        logger.info(f"Successfully processed file: {result['file']}")
        return result

    elif source_path.is_dir():
        logger.info(f"Processing directories: {source_path} .")
        results = {}

        valid_extensions = {".txt", ".pdf"}

        src_files = {f.name: f for f in source_path.glob("*") if f.is_file() and f.suffix in valid_extensions}

        # Compare matching files
        for filename in src_files.keys():
            src_file = src_files.get(filename)

            if src_file:
                logger.info(f"Processing {src_file} files from {source_path}")
                results[filename] =  f"processing file from directory with config file {config_data}"

        return results

    else:
        raise ValueError("Source must be a valid file, directory, or  string.")
