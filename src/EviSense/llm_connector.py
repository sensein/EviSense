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
# @File    : llm_connector.py
# @Software: PyCharm


import asyncio
import json
import httpx
import openai
import ollama

class LLMConnector:
    """
        A connector for interacting with various Large Language Model (LLM) providers asynchronously.

        Supported providers:
            - Ollama (local model)
            - OpenRouter (API-based)
            - OpenAI (API-based)

        The connector provides an interface to send prompts and retrieve generated responses from
        the selected provider.

        Attributes:
            provider (str): Name of the provider (e.g., 'ollama', 'openrouter', 'openai').
            api_key (str, optional): API key required for OpenRouter and OpenAI.
            model (str, optional): Model name to use for text generation.
            base_url (str, optional): Base URL for the API provider; defaults to standard endpoints.

        Methods:
            generate(prompt: str) -> str:
                Generates a response from the specified LLM provider asynchronously.

        Private Methods:
            _get_default_base_url() -> str:
                Returns the default base URL for the selected provider.

            _call_ollama(prompt: str) -> str:
                Sends a prompt to a locally hosted Ollama model.

            _call_openrouter(prompt: str) -> str:
                Sends a prompt to OpenRouter API.

            _call_openai(prompt: str) -> str:
                Sends a prompt to OpenAI API.

        Example Usage:
        --------------
        >>> connector = LLMConnector(provider="openai", api_key="your_api_key", model="gpt-4")
        >>> response = await connector.generate("Tell me a joke.")
        >>> print(response)

        Raises:
            ValueError: If an unsupported provider is specified.
        """
    def __init__(self, provider, api_key=None, model=None, base_url=None):
        """
        Initialize the LLM connector.

        :param provider: str, name of the provider (ollama, openrouter, openai)
        :param api_key: str, API key (if required)
        :param model: str, model name
        :param base_url: str, Base URL (required for Ollama, configurable for others)
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or self._get_default_base_url()

    def _get_default_base_url(self):
        """Set default base URLs if not explicitly provided."""
        if self.provider == "ollama":
            return "http://localhost:11434"
        elif self.provider == "openrouter":
            return "https://openrouter.ai/api/v1"
        elif self.provider == "openai":
            return "https://api.openai.com/v1"
        else:
            raise ValueError("Unsupported provider: Choose from 'ollama', 'openrouter', 'openai'.")

    async def generate(self, prompt):
        """
        Generate a response using the specified LLM asynchronously.

        :param prompt: str, input text
        :return: str, generated response
        """
        try:
            if self.provider == "ollama":
                return await self._call_ollama(prompt)
            elif self.provider == "openrouter":
                return await self._call_openrouter(prompt)
            elif self.provider == "openai":
                return await self._call_openai(prompt)
            else:
                raise ValueError("Unsupported provider: Choose from 'ollama', 'openrouter', 'openai'.")
        except Exception as e:
            return f"{self.provider.capitalize()} Error: {str(e)}"

    async def _call_ollama(self, prompt):
        """ Call a local Ollama LLM asynchronously using ollama-python. """
        try:
            response = await asyncio.to_thread(
                ollama.chat, model=self.model, messages=[{"role": "user", "content": prompt}]
            )
            return response.get("message", {}).get("content", "Error in Ollama response")
        except Exception as e:
            return f"Ollama API error: {e}"

    async def _call_openrouter(self, prompt):
        """ Call OpenRouter API asynchronously. """
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json().get("choices", [{}])[0].get("message", {}).get("content", "Error in OpenRouter response")
            except httpx.HTTPStatusError as e:
                return f"OpenRouter API error: {e.response.status_code} - {e.response.text}"
            except json.JSONDecodeError as e:
                return f"JSON decode error: {e} - Raw response: {response.text}"

    async def _call_openai(self, prompt):
        """ Call OpenAI API asynchronously. """
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json().get("choices", [{}])[0].get("message", {}).get("content", "Error in OpenAI response")
            except httpx.HTTPStatusError as e:
                return f"OpenAI API error: {e.response.status_code} - {e.response.text}"
            except json.JSONDecodeError as e:
                return f"JSON decode error: {e} - Raw response: {response.text}"