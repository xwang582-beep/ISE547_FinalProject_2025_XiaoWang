"""
Configuration file for FAQ Generator
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Model Settings
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

# Text Chunking Settings
MAX_TOKENS_PER_CHUNK = int(os.getenv("MAX_TOKENS_PER_CHUNK", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# FAQ Generation Settings
MAX_FAQS_PER_CHUNK = int(os.getenv("MAX_FAQS_PER_CHUNK", "3"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS_RESPONSE = int(os.getenv("MAX_TOKENS_RESPONSE", "1000"))

# Deduplication Settings
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))

# Output Settings
OUTPUT_DIR = "output"
TEMPLATE_DIR = "templates"

# Supported file formats
SUPPORTED_FORMATS = [".pdf", ".txt", ".md", ".docx"]

