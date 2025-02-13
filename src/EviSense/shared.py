# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# DISCLAIMER: This software is provided "as is" without any warranty,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose, and non-infringement.
#
# In no event shall the authors or copyright holders be liable for any
# claim, damages, or other liability, whether in an action of contract,
# tort, or otherwise, arising from, out of, or in connection with the
# software or the use or other dealings in the software.
# -----------------------------------------------------------------------------

# @Author  : Tek Raj Chhetri
# @Email   : tekraj@mit.edu
# @Web     : https://tekrajchhetri.com/
# @File    : shared.py
# @Software: PyCharm

import asyncio
from typing import Dict, Any
from .llm_connector import LLMConnector
import yaml
import logging
from pathlib import Path
from typing import Union, Dict, List
import textwrap
from GrobidArticleExtractor import GrobidArticleExtractor

logger = logging.getLogger(__name__)
async def call_llms_in_parallel(prompt: str, config: Dict[str, Any]) -> Dict[str, str]:
    """
    Calls multiple LLMs in parallel using the provided configuration dictionary and combines their results.

    Args:
        prompt (str): Input text for the LLMs
        config (Dict[str, Any]): Configuration dictionary containing LLM settings

    Returns:
        Dict[str, str]: Responses from each LLM
    """
    try:
        # Ensure config is a dictionary
        if isinstance(config, str):
            config = load_config(config)
        elif not isinstance(config, dict):
            raise ValueError("Config must be either a string path to YAML file or a dictionary")

        connectors = []
        llm_config = config.get("llm", {})
        if not llm_config:
            raise ValueError("No LLM configuration found in config")

        # Get the default provider (if defined)
        default_provider = llm_config.get("default")
        logger.info(f"Default provider: {default_provider}")

        for provider, provider_config in llm_config.items():
            if provider == "default":
                continue  # Skip the default provider key

            try:
                base_url = provider_config.get("base_url")
                api_key = provider_config.get("api_key", None)
                models = provider_config.get("models", [])

                # Use default_model if no explicit models are listed
                if not models:
                    default_model = provider_config.get("default_model")
                    if default_model:
                        models = [default_model]
                        logger.info(f"Using default model for {provider}: {default_model}")

                # Create LLM connectors for each model
                for model in models:
                    try:
                        connectors.append(
                            LLMConnector(
                                provider=provider,
                                model=model,
                                base_url=base_url,
                                api_key=api_key
                            )
                        )
                        logger.info(f"Added connector for {provider} with model {model}")
                    except Exception as e:
                        logger.error(f"Error creating connector for {provider} model {model}: {str(e)}")

            except Exception as e:
                logger.error(f"Error configuring provider {provider}: {str(e)}")

        # If no connectors were created and we have a default provider, try to use it
        if not connectors and default_provider and default_provider in llm_config:
            logger.info(f"No connectors created, falling back to default provider {default_provider}")
            default_config = llm_config[default_provider]
            try:
                base_url = default_config.get("base_url")
                api_key = default_config.get("api_key", None)
                default_model = default_config.get("default_model")

                if default_model:
                    connectors.append(
                        LLMConnector(
                            provider=default_provider,
                            model=default_model,
                            base_url=base_url,
                            api_key=api_key
                        )
                    )
                    logger.info(f"Added default connector for {default_provider} with model {default_model}")
            except Exception as e:
                logger.error(f"Error creating default connector: {str(e)}")

        if not connectors:
            raise ValueError("No valid LLM connectors could be created from configuration")

        # Execute all LLM calls concurrently
        tasks = [connector.generate(prompt) for connector in connectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        response_dict = {}
        for connector, result in zip(connectors, results):
            key = f"{connector.provider}_{connector.model}"
            if isinstance(result, Exception):
                logger.error(f"Error from {key}: {str(result)}")
                response_dict[key] = str(result)
            else:
                response_dict[key] = result

        return response_dict

    except Exception as e:
        logger.error(f"Error in call_llms_in_parallel: {str(e)}")
        raise



def load_config(config: Union[str, Path, Dict]) -> dict:
    """
    Loads the LLM configuration from a YAML file or directly from a dictionary.

    Args:
        config (Union[str, Path, dict]): The configuration source.

    Returns:
        dict: Parsed LLM configuration.

    Raises:
        FileNotFoundError: If the YAML file is not found.
        ValueError: If the input is not a valid YAML file or dictionary.
        yaml.YAMLError: If there is an error parsing the YAML configuration.
    """
    if isinstance(config, dict):
        return config  # Directly use the dictionary

    config_path = Path(config) if isinstance(config, str) else config
    if not config_path.exists() or config_path.suffix.lower() not in {".yml", ".yaml"}:
        raise ValueError(f"Invalid configuration: {config}. Expected a YAML file or a dictionary.")

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file {config}: {e}")


def make_prompt(term: Union[str, List[str]], document: str) -> str:
    """
    Creates a prompt for the LLM to analyze a document for specific terms.

    Args:
        term (Union[str, List[str]]): Term or list of terms to search for
        document (str): Document content to analyze

    Returns:
        str: Formatted prompt for the LLM
    """
    # Handle term being a list
    if isinstance(term, list):
        search_terms = ", ".join(f'"{t}"' for t in term)
    else:
        search_terms = f'"{term}"'


    return f"""
    You are a neuroscience expert performing an in-depth literature analysis. Your task is to read through the given document and extract the rationales and textual evidence that substantiate the given term(s).

    **Task Requirements:**
    For each given term:

    - **Search Across Given Text:** Analyze the provided text to locate sections where the term is discussed with supporting evidence.
    - **Extract References:** Identify and extract supporting text, including explanations, definitions, research findings, or conceptual justifications.
    - **Provide Metadata:** Document the exact section title where the supporting reference is found (excluding the paper title).
    - **Summarize Findings:** Write a concise summary explaining how the term is justified or supported in the literature, focusing on its context, significance, and implications.

    **Input Term(s):** {search_terms}

    **Document for Analysis:** 
    ```
    {document}
    ```

     **Output Format (Strictly return only this JSON structure, without any extra text):**
    {{
        "Term": "{search_terms}",
        "Rationale": [
            {{
                "Section": "<Subsection name, e.g., 'Introduction', 'Methods'>",
                "Text": "<Exact sentence or paragraph explaining why the term is relevant>"
            }}
        ],
        "Evidence": [
            {{
                "Section": "<Subsection name, e.g., 'Introduction', 'Methods'>",
                "Text": "<Exact sentence or paragraph supporting the term's presence or significance>"
            }}
        ],
        "Summary": "<Concise synthesis describing how the term is supported in the document, including context and significance>"
    }}

    **Important Notes:**
    - Do not truncate the extracted text.
    - Respond **only** with the dictionary in JSON format.
    - Do **not** include extra text, explanations, headings, or Markdown formatting.
    - Do **not** add "Output:", "```json", or any other wrapping text.
    - Your response should be a **pure JSON dictionary only**.
    - Ensure that section names are correctly recorded (not the paper title).
    - Maintain accuracy and clarity in the extracted references.
    - If multiple terms are provided, analyze each term separately and combine the results.

    Begin your analysis and start extracting textual evidence, explanations, and rationales that substantiate the given term(s).
    """


def extract_pdf_content(file_path: str) -> dict:
    """
        Extracts content from a PDF file using GrobidArticleExtractor.

        This function processes the given PDF file and extracts it contents.

        Args:
            file_path (str): The path to the PDF file.

        Returns:
            dict: A dictionary containing:
                - "metadata" (dict): Metadata information about the publications.
                - "sections" (list): A list of extracted sections, where each section is a dictionary containing:
                    - "heading" (str): The heading/title of the section.
                    - "content" (str): The textual content of the section.
        """
    extractor = GrobidArticleExtractor()
    xml_content = extractor.process_pdf(file_path)
    result = extractor.extract_content(xml_content)

    try:
        extracted_data = {
            "metadata": result.get("metadata", {}),
            "sections": []
        }

        # Process sections
        sections = result.get("sections", [])
        if not sections:
            logger.warning("No sections found in PDF")
            # Create a single section with all content if available
            if content := result.get("content"):
                sections = [{
                    "heading": "Content",
                    "content": content
                }]

        # Add sections to extracted data
        for section in sections:
            if not isinstance(section, dict):
                logger.warning(f"Skipping invalid section format: {type(section)}")
                continue
                
            heading = str(section.get("heading", "")).strip()
            content = str(section.get("content", "")).strip()
            
            if not content:
                logger.warning(f"Skipping empty section: {heading}")
                continue
                
            extracted_data["sections"].append({
                "heading": heading,
                "content": content
            })

        if not extracted_data["sections"]:
            raise Exception("No valid content could be extracted from PDF")

        logger.info(f"Successfully extracted {len(extracted_data['sections'])} sections")
        return extracted_data

    except Exception as e:
        logger.error(f"Error in extract_pdf_content: {str(e)}")
        raise


async def process_file(file_path: Path, config_data: dict, terms: Union[str, List[str]]) -> dict:
    """
    Processes an individual file based on the provided configuration.

    Args:
        file_path (Path): Path to the file to be processed.
        config_data (dict): Extracted configuration settings.
        terms (Union[str, List[str]]): Terms to search for in the file.

    Returns:
        dict: Extracted rationale or evidence.
    """
    try:
        # Validate inputs
        if not isinstance(file_path, (str, Path)):
            raise ValueError(f"Invalid file_path type: {type(file_path)}")
        if not isinstance(config_data, dict):
            raise ValueError(f"Invalid config_data type: {type(config_data)}")
        if not terms:
            raise ValueError("No search terms provided")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_path.suffix.lower() == ".pdf":
            logger.info(f"Processing PDF file: {file_path}")
            
            try:
                # Extract PDF content
                pdf_content = extract_pdf_content(str(file_path))
                if not pdf_content["sections"]:
                    raise ValueError("No content sections found in PDF")
                
                # Format sections for prompt
                formatted_sections = ""
                for section in pdf_content["sections"]:
                    heading = section.get("heading", "").strip()
                    content = section.get("content", "").strip()
                    if heading:
                        formatted_sections += f"\nSection: {heading}\n"
                    formatted_sections += f"{content}\n"
                
                if not formatted_sections.strip():
                    raise ValueError("No content extracted from PDF sections")
                
                # Create prompt with formatted content
                prompt = make_prompt(term=terms, document=formatted_sections)
                logger.info("Created prompt with formatted content")
                
                # Call LLMs and get response
                llm_response = await call_llms_in_parallel(prompt=prompt, config=config_data)
                if not llm_response:
                    raise ValueError("No response received from LLMs")
                
                return {
                    "file": str(file_path),
                    "status": "Processed",
                    "results": llm_response,
                }
                
            except Exception as e:
                logger.error(f"Error processing PDF content: {str(e)}")
                return {
                    "file": str(file_path),
                    "status": "Error",
                    "error": f"PDF processing error: {str(e)}"
                }
        
        logger.info(f"Unsupported file type: {file_path.suffix}")
        return {
            "file": str(file_path),
            "status": "Error",
            "error": f"Unsupported file type: {file_path.suffix}"
        }
        
    except Exception as e:
        logger.error(f"Error in process_file: {str(e)}")
        return {
            "file": str(file_path) if isinstance(file_path, (str, Path)) else "unknown",
            "status": "Error",
            "error": f"Processing error: {str(e)}"
        }

def process_string_source(string_text: str, config_data: dict) -> dict:
    """
    Processes a knowledge graph input from a string.

    Args:
        string_text (str): Input as string.
        config_data (dict): Extracted configuration settings.

    Returns:
        dict: Extracted rationale or evidence.
    """
    logger.info("Processing knowledge graph string input.")
    return {"graph": string_text[:100], "status": "Processed", "config": config_data}
