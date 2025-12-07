"""
Smart FAQ Generator - Main Application
Automatically generate FAQs from documents using LLMs
"""

import argparse
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.document_parser import DocumentParser
from src.text_chunker import TextChunker
from src.faq_generator import FAQGenerator
from src.output_formatter import OutputFormatter
import config


console = Console()


def print_banner():
    """Print application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║          Smart FAQ Generator v1.0                         ║
║     Automatically generate FAQs from documents using LLMs  ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def validate_api_key(provider: str = "openai") -> str:
    """
    Validate and get API key
    
    Args:
        provider: API provider ('openai' or 'anthropic')
        
    Returns:
        API key
    """
    if provider == "openai":
        api_key = config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("[red]Error: OpenAI API key not found![/red]")
            console.print("Please set OPENAI_API_KEY environment variable or add it to .env file")
            sys.exit(1)
    elif provider == "anthropic":
        api_key = config.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            console.print("[red]Error: Anthropic API key not found![/red]")
            console.print("Please set ANTHROPIC_API_KEY environment variable or add it to .env file")
            sys.exit(1)
    else:
        console.print(f"[red]Error: Unsupported provider '{provider}'[/red]")
        sys.exit(1)
    
    return api_key


def process_document(
    input_file: str,
    output_file: str,
    provider: str = "openai",
    model: str = None,
    max_faqs: int = None,
    output_format: str = "all",
    verbose: bool = True
):
    """
    Process a document and generate FAQs
    
    Args:
        input_file: Path to input document
        output_file: Base name for output files
        provider: LLM provider
        model: Model name
        max_faqs: Maximum FAQs per chunk
        output_format: Output format(s)
        verbose: Whether to print detailed progress
    """
    # Validate API key
    api_key = validate_api_key(provider)
    
    # Set defaults
    if model is None:
        model = config.MODEL_NAME
    if max_faqs is None:
        max_faqs = config.MAX_FAQS_PER_CHUNK
    
    # Initialize components
    parser = DocumentParser()
    chunker = TextChunker(
        max_tokens=config.MAX_TOKENS_PER_CHUNK,
        overlap=config.CHUNK_OVERLAP,
        model=model
    )
    generator = FAQGenerator(
        api_key=api_key,
        model=model,
        max_faqs_per_chunk=max_faqs,
        temperature=config.TEMPERATURE,
        provider=provider
    )
    formatter = OutputFormatter(output_dir=config.OUTPUT_DIR)
    
    try:
        # Step 1: Parse document
        if verbose:
            console.print(f"\n[bold cyan]Step 1: Parsing document...[/bold cyan]")
            console.print(f"Input file: {input_file}")
        
        file_info = parser.get_file_info(input_file)
        if verbose:
            info_table = Table(show_header=False, box=None)
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="white")
            info_table.add_row("File name", file_info['filename'])
            info_table.add_row("Format", file_info['format'])
            info_table.add_row("Size", f"{file_info['size_kb']} KB")
            console.print(info_table)
        
        text = parser.parse(input_file)
        
        if verbose:
            console.print(f"✓ Extracted {len(text)} characters")
        
        # Step 2: Chunk text
        if verbose:
            console.print(f"\n[bold cyan]Step 2: Chunking text...[/bold cyan]")
        
        chunks = chunker.chunk_text(text)
        stats = chunker.get_statistics(chunks)
        
        if verbose:
            stats_table = Table(show_header=False, box=None)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="white")
            stats_table.add_row("Total chunks", str(stats['total_chunks']))
            stats_table.add_row("Total tokens", str(stats['total_tokens']))
            stats_table.add_row("Avg tokens/chunk", str(stats['avg_tokens']))
            console.print(stats_table)
        
        # Step 3: Generate FAQs
        if verbose:
            console.print(f"\n[bold cyan]Step 3: Generating FAQs...[/bold cyan]")
            console.print(f"Using {provider} with model: {model}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            if verbose:
                task = progress.add_task(f"Processing {len(chunks)} chunks...", total=None)
            
            all_faqs = generator.generate_faqs_batch(chunks, verbose=verbose)
            
            if verbose:
                progress.update(task, completed=True)
        
        if not all_faqs:
            console.print("[yellow]Warning: No FAQs were generated![/yellow]")
            return
        
        if verbose:
            console.print(f"✓ Generated {len(all_faqs)} FAQs")
        
        # Step 4: Deduplicate and rank
        if verbose:
            console.print(f"\n[bold cyan]Step 4: Deduplicating and ranking...[/bold cyan]")
        
        unique_faqs = generator.deduplicate_faqs(
            all_faqs,
            similarity_threshold=config.SIMILARITY_THRESHOLD
        )
        
        if verbose:
            console.print(f"✓ Removed {len(all_faqs) - len(unique_faqs)} duplicate FAQs")
        
        ranked_faqs = generator.rank_faqs(unique_faqs)
        
        # Step 5: Generate outputs
        if verbose:
            console.print(f"\n[bold cyan]Step 5: Generating output files...[/bold cyan]")
        
        output_base = Path(output_file).stem
        source_filename = Path(input_file).name
        
        created_files = []
        
        if output_format in ["all", "markdown", "md"]:
            md_path = formatter.to_markdown(
                ranked_faqs,
                f"{output_base}.md",
                title=f"FAQs: {source_filename}",
                source_file=source_filename
            )
            created_files.append(md_path)
            if verbose:
                console.print(f"✓ Markdown: {md_path}")
        
        if output_format in ["all", "html"]:
            html_path = formatter.to_html(
                ranked_faqs,
                f"{output_base}.html",
                title=f"FAQs: {source_filename}",
                source_file=source_filename
            )
            created_files.append(html_path)
            if verbose:
                console.print(f"✓ HTML: {html_path}")
        
        if output_format in ["all", "json"]:
            json_path = formatter.to_json(
                ranked_faqs,
                f"{output_base}.json",
                metadata={
                    'source_file': source_filename,
                    'model': model,
                    'provider': provider,
                    'chunks': len(chunks)
                }
            )
            created_files.append(json_path)
            if verbose:
                console.print(f"✓ JSON: {json_path}")
        
        if output_format in ["all", "txt", "text"]:
            txt_path = formatter.to_txt(
                ranked_faqs,
                f"{output_base}.txt",
                title=f"FAQs: {source_filename}"
            )
            created_files.append(txt_path)
            if verbose:
                console.print(f"✓ Text: {txt_path}")
        
        # Success summary
        console.print("\n" + "="*60)
        console.print(Panel.fit(
            f"[bold green]✓ Successfully generated {len(ranked_faqs)} FAQs![/bold green]\n"
            f"Output files created: {len(created_files)}",
            title="Success",
            border_style="green"
        ))
        
    except FileNotFoundError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        import traceback
        if verbose:
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Smart FAQ Generator - Automatically generate FAQs from documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python main.py --input document.pdf --output faqs

  # Use Anthropic Claude
  python main.py --input doc.pdf --output faqs --provider anthropic --model claude-3-haiku-20240307

  # Generate only HTML output
  python main.py --input doc.pdf --output faqs --format html

  # Control FAQ quantity
  python main.py --input doc.pdf --output faqs --max-faqs 5
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input document path (PDF, TXT, MD, or DOCX)'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output file base name (without extension)'
    )
    
    parser.add_argument(
        '--provider', '-p',
        choices=['openai', 'anthropic'],
        default='openai',
        help='LLM provider (default: openai)'
    )
    
    parser.add_argument(
        '--model', '-m',
        help='Model name (default: gpt-3.5-turbo for OpenAI, claude-3-haiku for Anthropic)'
    )
    
    parser.add_argument(
        '--max-faqs',
        type=int,
        help=f'Maximum FAQs per chunk (default: {config.MAX_FAQS_PER_CHUNK})'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['all', 'markdown', 'md', 'html', 'json', 'txt', 'text'],
        default='all',
        help='Output format (default: all)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Smart FAQ Generator v1.0'
    )
    
    args = parser.parse_args()
    
    # Print banner
    if args.verbose:
        print_banner()
    
    # Process document
    process_document(
        input_file=args.input,
        output_file=args.output,
        provider=args.provider,
        model=args.model,
        max_faqs=args.max_faqs,
        output_format=args.format,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()

