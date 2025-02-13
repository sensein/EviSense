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
    Calls multiple LLMs in parallel with configurations from config.yml and combines their results in a dictionary.

    Args:
        prompt (str): Input text for the LLMs
        config (Dict[str, Any]): Configuration dictionary containing LLM settings
            Expected format:
            {
                "llm": {
                    "ollama": {
                        "base_url": "http://localhost:11434",
                        "models": ["deepseek-r1:14b", "qwen2.5-coder:14b"]
                    },
                    "openrouter": {
                        "api_key": "your-openrouter-key",
                        "base_url": "https://openrouter.ai/api/v1",
                        "model": "gpt-4"
                    },
                    "openai": {
                        "api_key": "your-openai-key",
                        "base_url": "https://api.openai.com/v1",
                        "model": "gpt-4"
                    }
                }
            }

    Returns:
        Dict[str, str]: Responses from each LLM
    """
    connectors = []

    # Configure Ollama models
    if "ollama" in config["llm"]:
        ollama_config = config["llm"]["ollama"]
        for model in ollama_config["models"]:
            connectors.append(
                LLMConnector(
                    provider="ollama",
                    model=model,
                    base_url=ollama_config["base_url"]
                )
            )

    # Configure OpenRouter
    if "openrouter" in config["llm"]:
        openrouter_config = config["llm"]["openrouter"]
        connectors.append(
            LLMConnector(
                provider="openrouter",
                api_key=openrouter_config["api_key"],
                model=openrouter_config["model"],
                base_url=openrouter_config["base_url"]
            )
        )

    # Configure OpenAI
    if "openai" in config["llm"]:
        openai_config = config["llm"]["openai"]
        connectors.append(
            LLMConnector(
                provider="openai",
                api_key=openai_config["api_key"],
                model=openai_config["model"],
                base_url=openai_config["base_url"]
            )
        )

    # Execute all LLM calls concurrently
    tasks = [connector.generate(prompt) for connector in connectors]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to error messages and create response dictionary
    response_dict = {}
    for connector, result in zip(connectors, results):
        key = f"{connector.provider}_{connector.model}"
        response_dict[key] = str(result) if isinstance(result, Exception) else result

    return response_dict


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


def make_prompt(terms, pdf_text):

    prompt = textwrap.dedent("""
        You are a neuroscience expert performing an in-depth literature analysis. Your task is to locate and extract references that support a given neuroscience-related term across given text. This involves not just identifying the term's occurrences but also finding textual evidence, explanations, and rationales that substantiate its meaning, significance, or application.

        Task Requirements:
        For each given term:
        
        Search Across given text: Analyze the provided text to locate sections where the term is discussed with supporting evidence.
        
        Extract References: Identify and extract supporting text, including explanations, definitions, research findings, or conceptual justifications.
        
        Provide Metadata: Document the exact section tile and paper title where the supporting reference is found.
        
        Summarize Findings: Write a concise summary explaining how the term is justified or supported in the literature, focusing on its context, significance, and implications.
        
        
        
        
        Term: {0}
        
        Input: {1}
        
        
        Output Format:
        
        For each term, return:
        
        Term: (Neuroscience term being analyzed)
        Document: (Title/Name of the PDF where it was found)
        Extracted Text: (Exact sentence/paragraph containing the rationale)
        Summary: (Concise explanation of how the term is supported in the document, including context and significance)
        
        Do not truncate the text extracted.
    """).format(terms, pdf_text)

    print(prompt)

    return prompt


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

    extracted_data = {
        "metadata": result.get("metadata", {}),
        "sections": []
    }

    for section in result.get("sections", []):
        extracted_section = {
            "heading": section.get("heading", ""),
            "content": section.get("content", "")
        }
        extracted_data["sections"].append(extracted_section)

    return extracted_data


def process_file(file_path: Path, config_data: dict, terms:Union[str, List[str]]) -> dict:
    """
    Processes an individual file based on the provided configuration.

    Args:
        file_path (Path): Path to the file to be processed.
        config_data (dict): Extracted configuration settings.

    Returns:
        dict: Extracted rationale or evidence.
    """
    file_path = Path(file_path)
    if file_path.suffix.lower() == ".pdf":
        return call_llms_in_parallel(prompt=make_prompt(terms=terms, pdf_text=extract_pdf_content(file_path)), config=config_data)


    logger.info(f"Extracting rationale from file: {file_path}")
    return {"file": str(file_path), "status": "Processed", "config": config_data}

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

