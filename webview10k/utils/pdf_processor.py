import asyncio
from pathlib import Path
from typing import Dict, Any, Tuple
from ..config import log
import json
import re
import pandas as pd
import fitz


async def get_pdf_metadata_async(pdf_path: Path, data_dir: Path) -> Dict[str, Any]:
    """
    Process PDF file asynchronously to extract metadata.

    Args:
        pdf_path (Path): Path to the PDF file
        data_dir (Path): Directory where metadata should be stored

    Returns:
        Dict[str, Any]: Dictionary containing metadata including:
            - num_pages: Total number of pages
            - preview: Text from first page
            - filename: Name of PDF file
            - fiscal_year_date: Date of fiscal year
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, get_pdf_metadata, pdf_path, data_dir)
    return result


def get_pdf_metadata(pdf_path: Path, data_dir: Path) -> Dict[str, Any]:
    """
    Extract metadata from PDF file.

    Args:
        pdf_path (Path): Path to PDF file
        data_dir (Path): Directory containing pdf_info.json

    Returns:
        Dict[str, Any]: Dictionary containing:
            - num_pages: Total number of pages
            - preview: First page text
            - filename: PDF filename
            - fiscal_year_date: Fiscal year date
    """
    first_page = get_page_texts(pdf_path, 0)
    if not data_dir / "pdf_info.json":
        pdf_info = get_pdf_info(pdf_path, data_dir)
    else:
        with open(data_dir / "pdf_info.json", "r", encoding="utf-8") as f:
            pdf_info = json.load(f)
    metadata = pdf_info.get("metadata")
    return {
        "num_pages": metadata["length"],
        "preview": first_page,
        "filename": pdf_path.name,
        "fiscal_year_date": metadata["fiscal_year_date"],
    }


def get_pdf_info(pdf_path: Path, output_dir: Path) -> Dict[str, Dict[str, int]]:
    """
    Extract index and metadata from PDF file.

    Args:
        pdf_path (Path): Path to PDF file
        output_dir (Path): Directory to save extracted information

    Returns:
        Dict[str, Dict[str, int]]: Dictionary containing:
            - index: Information about document sections
            - metadata: Document metadata including fiscal year

    Notes:
        Saves extracted information to pdf_info.json in output directory
    """

    length = len(fitz.open(pdf_path))
    index_text = ""
    fiscal_year_date = None

    fiscal_year_patterns = [
        r"(?:For\s+)?(?:the\s+)?(?:Fiscal\s+)?Year\s+Ended\s+(?:December|January|February|March|April|May|June|July|August|September|October|November)\s+\d{1,2}(?:,\s+|\s+)\d{4}",
        r"FISCAL\s+YEAR\s+ENDED\s+(?:DECEMBER|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER)\s+\d{1,2}(?:,\s+|\s+)\d{4}",
    ]
    for page_num in range(min(10, length)):
        text = get_page_texts(pdf_path, page_num).replace("**", " ")
        if "PART I" in text and "Item 1." in text:
            index_text = text
            # Try each fiscal year pattern
            for pattern in fiscal_year_patterns:
                date_match = re.search(pattern, text, re.IGNORECASE)
                if date_match:
                    fiscal_year_date = date_match.group().strip()
                    print(f"Found fiscal year: {fiscal_year_date}")
                    break

            # If not found in the immediate context, look for specific form text
            if not fiscal_year_date:
                form_date_match = re.search(
                    r"For\s+the\s+Year\s+Ended\s+(?:December|January|February|March|April|May|June|July|August|September|October|November)\s+\d{1,2}(?:,\s+|\s+)\d{4}",
                    text,
                    re.IGNORECASE,
                )
                if form_date_match:
                    fiscal_year_date = form_date_match.group().strip()
                    print(f"Found fiscal year from form header: {fiscal_year_date}")
            break

    if not index_text:
        raise ValueError("Could not find index in first 10 pages")

    # Parse the index content
    index_dict = {}
    current_part = None

    # Split text into lines and process each line
    lines = index_text.split("\n")
    for line in lines:
        # Check for PART markers
        if re.match(r"^PART [I|V]+", line):
            current_part = line.strip()
            continue

        # Match item lines
        match = re.match(r"\s*Item (\d+[A-Z]?)\.\s*(.*?)\s+(\d+)\s*$", line.strip())
        if match:
            item_num, description, page = match.groups()
            item_key = f"Item {item_num}"
            index_dict[item_key] = {
                "description": description.strip(),
                "start_page": int(page),
                "end_page": int(page),  # Initialize end_page as same as start_page
                "part": current_part,
            }

    # Calculate end pages
    items = sorted(index_dict.items(), key=lambda x: x[1]["start_page"])
    for i in range(len(items) - 1):
        current_item = items[i][0]
        next_item = items[i + 1][0]
        current_start = index_dict[current_item]["start_page"]
        next_start = index_dict[next_item]["start_page"]

        # If items are in the same part, include overlap
        if index_dict[current_item]["part"] == index_dict[next_item]["part"]:
            if next_start > current_start:  # Different pages
                index_dict[current_item]["end_page"] = next_start  # Include overlap
        else:
            # Different parts, only overlap if not on same page
            if next_start > current_start:
                index_dict[current_item]["end_page"] = next_start - 1
    pdf_info = {
        "index": index_dict,
        "metadata": {
            "fiscal_year_date": fiscal_year_date,
            "file_name": pdf_path.name,
            "length": length,
        },
    }
    # Save to JSON file
    output_file = output_dir / "pdf_info.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(pdf_info, f, indent=2)

    return pdf_info


async def process_pdf_async(pdf_path: Path, output_dir: Path) -> None:
    """
    Asynchronously process PDF file to extract sections.

    Args:
        pdf_path (Path): Path to PDF file
        output_dir (Path): Directory to save extracted sections

    Notes:
        Runs process_pdf in thread pool executor
    """
    loop = asyncio.get_event_loop()
    try:

        await loop.run_in_executor(None, process_pdf, pdf_path, output_dir)
        log.info("split the sections out successfully")
    except Exception as e:
        log.error(f"Could not save sections: {e}")


def process_pdf(pdf_path: Path, output_dir: Path) -> None:
    """
    Process PDF file and extract sections based on index.

    Args:
        pdf_path (Path): Path to PDF file
        output_dir (Path): Directory to save extracted sections

    Notes:
        - Requires pdf_info.json file in output directory
        - Saves each section as separate text file
        - Creates full text version with page breaks
    """
    if not (output_dir / "pdf_info.json").exists():
        log.error("info file not found. Please extract the index first.")
    else:
        with open(output_dir / "pdf_info.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            index = data["index"]
    try:
        for item, details in index.items():
            start_page = details["start_page"] + 1
            end_page = details["end_page"] + 2
            # section_pdf = pdf.pages[start_page:end_page]
            log.info(f"Extracting section {item} from pages {start_page} to {end_page}")

            # gets all text from the section's pages
            text = get_page_texts(pdf_path, start_page, end_page)

            # Find the start of the current item
            start_pattern = f"\*\*{item.upper()}\\."
            start_match = re.search(start_pattern, text)
            if not start_match:
                log.warning(f"Could not find start marker for {item}")
                continue
            next_item_pattern = r"\*\*ITEM \d+[A-Z]?\."
            next_matches = list(
                re.finditer(next_item_pattern, text[start_match.end() :])
            )

            if next_matches:
                # Take text up to the next item
                text = text[
                    start_match.start() : start_match.end() + next_matches[0].start()
                ]
            else:
                # Take all remaining text if this is the last item
                text = text[start_match.start() :]

            section_path = output_dir / f"{item}.txt"
            with open(section_path, "w", encoding="utf-8") as f:
                f.write(text)
    except Exception as e:
        log.error(f"Error splitting sections: {e}", exc_info=True)

    try:
        text_with_formatting = extract_text_with_formatting(pdf_path)
        text_by_page = create_text_by_page(text_with_formatting)
        full_text = "\n\n======= Page Break =======\n\n".join(text_by_page)
        with open(output_dir / "10k_full_text.txt", "w") as f:
            f.write(full_text)

    except Exception as e:
        log.error(f"saving full text error {e}", exc_info=True)


## fitz / pymupdf functions
def extract_text_with_formatting(pdf_path:Path, pages:list=None) -> list:
    """
    Extract text from PDF while preserving formatting information.

    Args:
        pdf_path (Path): Path to PDF file
        pages (list, optional): List of page numbers to extract. Defaults to all pages.

    Returns:
        list: List of dictionaries containing text blocks with formatting info:
            - page: Page number
            - text: Actual text content
            - font_size: Size of font used
            - is_bold: Boolean indicating bold text
            - is_italic: Boolean indicating italic text
            - bbox: Bounding box coordinates
    """
    doc = fitz.open(pdf_path)
    extracted_data = []
    if pages is None:
        pages = range(len(doc))

    for page_num in pages:
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]  # Extract text as structured blocks
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Extract text, font size, and whether it's bold/italic
                        text = span["text"]
                        font_size = span["size"]
                        is_bold = "Bold" in span["font"]
                        is_italic = "Italic" in span["font"]
                        bbox = span["bbox"]  # Bounding box (location on the page)
                        extracted_data.append(
                            {
                                "page": page_num + 1,
                                "text": text,
                                "font_size": font_size,
                                "is_bold": is_bold,
                                "is_italic": is_italic,
                                "bbox": bbox,
                            }
                        )
    return extracted_data

def create_text_by_page(formatted_text:list) -> str:
    """
    Convert formatted text blocks into properly formatted page text.

    Args:
        formatted_text (list): List of dictionaries containing text blocks with formatting

    Returns:
        str: Text organized by pages with proper spacing and formatting preserved
    """
    text_by_pages = {}

    # First, organize text by pages and lines
    for item in formatted_text:
        page = item["page"]
        if page not in text_by_pages:
            text_by_pages[page] = []

        x, y = item["bbox"][0], item["bbox"][1]  # Get x, y coordinates
        text = item["text"]
        if item["is_bold"]:
            text = f"**{text}**"
        if item["is_italic"]:
            text = f"*{text}*"

        text_by_pages[page].append({"x": x, "y": y, "text": text})

    # Process each page
    full_text = []
    for page in sorted(text_by_pages.keys()):
        # Sort items by y coordinate (vertically) first, then x coordinate
        items = text_by_pages[page]

        # Group items by similar y-coordinates (tolerance of 5 points)
        y_grouped = {}
        for item in items:
            y_key = round(item["y"] / 5) * 5  # Round to nearest 5
            if y_key not in y_grouped:
                y_grouped[y_key] = []
            y_grouped[y_key].append(item)

        # Sort each line by x coordinate
        page_lines = []
        for y in sorted(y_grouped.keys()):
            line_items = sorted(y_grouped[y], key=lambda x: x["x"])

            # Calculate spaces between items
            line_text = ""
            prev_end = 0
            for item in line_items:
                # Add appropriate spacing
                spaces = max(
                    int((item["x"] - prev_end) / 4), 1
                )  # Adjust divisor for spacing
                line_text += " " * spaces + item["text"]
                prev_end = item["x"] + len(item["text"]) * 4  # Approximate text width

            page_lines.append(line_text.rstrip())

        # Join lines for this page
        page_text = "\n".join(page_lines)
        full_text.append(page_text)

    # Join all pages with page breaks
    return full_text

def clean_text(text:str) -> str:
    """
    Clean extracted text by removing unwanted elements.

    Args:
        text (str): Raw text to clean

    Returns:
        str: Cleaned text with removed:
            - Lines containing only numbers
            - "Table of Contents" lines
    """ 
    # remove lines that are just numbers
    text = "\n".join(
        line for line in text.split("\n") if not line.replace(" ", "").isdigit()
    )
    # remove all lines that say "Table of Contents"
    text = "\n".join(
        line for line in text.split("\n") if line.strip() != "Table of Contents"
    )
    return text


def get_page_texts(pdf_path: Path, start_idx: int, end_idx: int = None) -> str:
    """
    Extract text from a range of pages in a PDF.

    Args:
        pdf_path (Path): Path to PDF file
        start_idx (int): Starting page index
        end_idx (int, optional): Ending page index. Defaults to start_idx + 1

    Returns:
        str: Concatenated text from specified page range with formatting preserved

    Raises:
        AssertionError: If page indices are invalid
    """
    if end_idx is None:
        end_idx = start_idx + 1

    assert start_idx < end_idx, "End index must be greater than start index"
    assert start_idx >= 0, "Start index must be greater than or equal to 0"
    assert end_idx <= len(
        fitz.open(pdf_path)
    ), "End index must be less than the number of pages in the PDF"

    text_with_formatting = extract_text_with_formatting(
        pdf_path, pages=range(start_idx, end_idx)
    )
    text_pages = create_text_by_page(text_with_formatting)
    text_pages = [clean_text(page) for page in text_pages]
    return "\n".join(text_pages)


# finance table extraction
def extract_table(text:str) -> Tuple[pd.DataFrame, str]:
    """
    Extract financial table data from text and convert to pandas DataFrame.

    Args:
        text (str): Raw text containing financial table data

    Returns:
        Tuple[pd.DataFrame, str]: Tuple containing:
            - DataFrame with financial data
            - String indicating unit of measurement (e.g. "in thousands")
    """
    table_text = text.replace("$", " ")

    # Extract the unit (e.g., "in thousands")
    unit_pattern = r"\((.*?)\)"
    unit_match = re.search(unit_pattern, table_text)
    unit = unit_match.group(1) if unit_match else "Unknown unit"

    # Extract the years (columns)
    year_pattern = r"\*\*(\d{4})\*\*"
    years = re.findall(year_pattern, table_text)

    # Extract rows dynamically
    row_pattern = r"^(.*?)\s+([\d,()\-]+)\s+([\d,()\-]+)\s*([\d,()\-]+)?$"
    matches = re.findall(row_pattern, table_text, re.MULTILINE)

    # Create a DataFrame
    columns = ["Category"] + years[
        : len(matches[0]) - 1
    ]  # Dynamically adjust columns based on years
    data = []

    for match in matches:
        category = match[0].strip()
        values = [
            match[i].replace(",", "").replace("(", "-").replace(")", "").strip("$")
            for i in range(1, len(match))
            if match[i]
        ]
        data.append([category] + [float(value) for value in values])

    df = pd.DataFrame(data, columns=columns)
    return df, unit


def get_finance_tables(data_dir: Path) -> list:
    """
    Extract all financial tables from a 10-K filing.

    Args:
        data_dir (Path): Directory containing the 10-K text file

    Returns:
        list: List of dictionaries containing financial tables:
            - statement: Name of financial statement
            - unit: Unit of measurement
            - data: Table data as list of records

    Notes:
        Processes Balance Sheets, Income Statements, and Cash Flow Statements
    """
    with open(data_dir / "10k_full_text.txt", "r") as file:
        form_10k_text = file.read()

    # Preprocess text: remove extra spaces and newlines
    cleaned_text = re.sub(r"\s+", " ", form_10k_text)
    # Extract financial statement names and page numbers using regex
    pattern = r"(Balance Sheets|Statements of Operations and Comprehensive Loss|Statements of Cash Flows).*?(F-\d+)"
    matches = re.findall(pattern, cleaned_text)

    pages = form_10k_text.split("\n\n======= Page Break =======\n\n ")

    # Convert matches into a DataFrame
    df = pd.DataFrame(matches, columns=["Statement", "Page"]).drop_duplicates()
    tables = []
    for i, row in df.iterrows():
        log.info(f"Finding finance table {row['Statement']}: on page {row['Page']}")
        text = ""
        for i, page in enumerate(pages):
            # find the page number
            if page.strip().endswith(row["Page"]):
                text = page
                break

        df, unit = extract_table(text)
        tables.append(
            {
                "statement": row["Statement"],
                "unit": unit,
                "data": df.to_dict(orient="records"),
            }
        )
    log.info(f"Found {len(tables)} finance tables")
    return tables
