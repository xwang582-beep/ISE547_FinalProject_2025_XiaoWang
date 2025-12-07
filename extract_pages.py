"""
Extract first N pages from a PDF file
"""

import sys
from pathlib import Path

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    print("PyPDF2 not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    from PyPDF2 import PdfReader, PdfWriter


def extract_pages(input_pdf, output_pdf, num_pages=50):
    """
    Extract first N pages from a PDF
    
    Args:
        input_pdf: Input PDF file path
        output_pdf: Output PDF file path
        num_pages: Number of pages to extract
    """
    try:
        # Read the input PDF
        reader = PdfReader(input_pdf)
        total_pages = len(reader.pages)
        
        print(f"📄 Input PDF: {input_pdf}")
        print(f"📊 Total pages: {total_pages}")
        print(f"✂️  Extracting first {min(num_pages, total_pages)} pages...")
        
        # Create a PDF writer
        writer = PdfWriter()
        
        # Add the first N pages
        for page_num in range(min(num_pages, total_pages)):
            writer.add_page(reader.pages[page_num])
            if (page_num + 1) % 10 == 0:
                print(f"   Processed {page_num + 1} pages...")
        
        # Write to output file
        with open(output_pdf, 'wb') as output_file:
            writer.write(output_file)
        
        output_size = Path(output_pdf).stat().st_size / (1024 * 1024)
        print(f"✅ Success! Created: {output_pdf}")
        print(f"📦 Output size: {output_size:.2f} MB")
        print(f"📄 Pages extracted: {min(num_pages, total_pages)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pages.py <input_pdf> [output_pdf] [num_pages]")
        print("Example: python extract_pages.py input.pdf output.pdf 50")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None
    num_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    
    # Default output name
    if not output_pdf:
        input_path = Path(input_pdf)
        output_pdf = str(input_path.parent / f"{input_path.stem}_first{num_pages}pages.pdf")
    
    extract_pages(input_pdf, output_pdf, num_pages)

