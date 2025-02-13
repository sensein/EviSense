# EviSense

EviSense is a Python library developed as a part of BrainKB project designed to extract evidence and rationales for specific terms within documents, including scientific publications. It enables efficient retrieval of relevant information from various sources, supporting multiple LLM providers and concurrent processing.


## Features

- Extract evidence and rationale from PDF documents, raw text, and directories
- Support for multiple LLM providers, including Ollama and OpenRouter and multiple models
- Flexible term search – retrieve insights for single or multiple terms efficiently

## Installation

```bash
pip install evisense
```
## Requirements
- Since it uses GrobidArticleExtractor, you must have Grobid running either locally or provide the remote Grobid Server url.

## Usage

### Input Types

1. PDF Files:
```bash
# Using absolute path
evisense-cli extract-evidence --config config.yml --source /full/path/to/paper.pdf --terms "Neuron"

# Using relative path (relative to current directory)
evisense-cli extract-evidence --config config.yml --source documents/paper.pdf --terms "Neuron"
```

2. Multiple Terms:
```bash
# Using JSON array
evisense-cli extract-evidence --config config.yml --source paper.pdf --terms '["Astrocyte","Ependymal"]'

# Using comma-separated values
evisense-cli extract-evidence --config config.yml --source paper.pdf --terms "Astrocyte,Ependymal"
```

3. Directory of PDFs:
```bash
evisense-cli extract-evidence --config config.yml --source path/to/papers/ --terms "Neuron"
```

4. Raw Text Input:
```bash
# Short text
evisense-cli extract-evidence --config config.yml --source "This is a neuroscience text..." --terms "Neuron"
```

### Configuration Options

- `provider`: (Optional) Specifies which provider to use ("all" or specific provider name)
- `default`: Default provider to use in these scenarios:
  1. When no provider is specified
  2. When the specified provider fails to initialize
  3. When authentication fails (e.g., invalid/missing API keys)
  4. When all selected providers return errors
- For each provider:
  - `base_url`: API endpoint
  - `api_key`: Authentication key (if required)
  - `models`: List of models to use
  - `default_model`: Default model if no specific models listed

### Example Configuration

```yaml
llm:
  default: "ollama"  # Specifies the default LLM provider
  provider: "openrouter" #select provider to use, e.g., ollama or openrouter. the value all will make use of all the providers specified in config in current case ollama and openrouter

  ollama:
    base_url: "http://localhost:11434"
    default_model: "deepseek-r1:14b"  # Default model for Ollama
    models:
      - "deepseek-r1:14b"
      - "qwen2.5-coder:14b"

  openrouter:
    api_key: "sk-or-v1"
    base_url: "https://openrouter.ai/api/v1"
    default_model: "gpt-4"  # Default model for OpenRouter
    models:
      - "gpt-4"
      - "gpt-4-turbo"

  grobid_server_url: "http://localhost:8070" #optional, if not specified, uses the default one http://http://localhost:8070

```


## Development

### Setup

```bash
git clone https://github.com/yourusername/EviSense.git
cd EviSense
pip install -e ".[dev]"
```

### Testing



## License

MIT License
