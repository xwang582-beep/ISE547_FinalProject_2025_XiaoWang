# Smart FAQ Generator

Automatically generate FAQs from documents using Large Language Models.

## Features
- Multi-format support: PDF, TXT, Markdown, DOCX
- Intelligent text chunking with context preservation
- LLM-powered FAQ generation
- Quality control and deduplication
- Multiple output formats: Markdown, HTML, JSON

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your API key:
```bash
cp .env.example .env
# Edit .env and add your OpenAI or Anthropic API key
```

## Usage

Basic usage:
```bash
python main.py --input path/to/document.pdf --output output/faqs.md
```

With custom options:
```bash
python main.py --input document.pdf --output faqs.md --max-faqs 25 --model gpt-3.5-turbo
```

## Project Structure
```
faq_generator/
├── src/                    # Source code modules
│   ├── document_parser.py  # Document parsing
│   ├── text_chunker.py     # Text chunking logic
│   ├── faq_generator.py    # LLM-based FAQ generation
│   └── output_formatter.py # Output formatting
├── templates/              # HTML templates
├── test_documents/         # Test documents
├── output/                 # Generated FAQs
├── main.py                 # Main CLI application
└── requirements.txt        # Python dependencies
```

## Requirements
- Python 3.9+
- OpenAI API key or Anthropic API key

