import asyncio
from pathlib import Path
import pdfplumber
from typing import Dict, Any

async def process_pdf_async(pdf_path: Path) -> Dict[str, Any]:
    """
    Process PDF file asynchronously
    Returns a dictionary with the processing results
    """
    # Run the CPU-intensive PDF processing in a thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, process_pdf_sync, pdf_path)
    return result

def process_pdf_sync(pdf_path: Path) -> Dict[str, Any]:
    """
    Synchronous PDF processing function that runs in a thread pool
    """
    with pdfplumber.open(pdf_path) as pdf:
        # Get basic PDF info
        num_pages = len(pdf.pages)
        
        # Extract text from first page as preview
        first_page = pdf.pages[0].extract_text() if num_pages > 0 else ""
        
        return {
            'num_pages': num_pages,
            'preview': first_page[:1000],  # First 500 chars as preview
            'filename': pdf_path.name
        }