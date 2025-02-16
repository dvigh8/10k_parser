from flask import Blueprint, jsonify, current_app
import asyncio
from ..utils.pdf_processor import get_pdf_metadata_async, get_finance_tables
from ..config import log
import aiofiles
import re
import pandas as pd

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/info/<string:filename>", methods=["POST"])
async def process_pdf(filename: str):
    """Process a PDF file asynchronously and extract metadata.
    
    Args:
        filename (str): Name of the PDF file to process
        
    Returns:
        flask.Response: JSON response containing:
            - status (str): 'success' or 'error'
            - filename (str): Name of processed file
            - result (dict): Extracted metadata
            
    Raises:
        404: If file is not found
        500: If processing fails
    """
    try:
        pdf_path = current_app.config["UPLOAD_FOLDER"] / filename
        data_dir = current_app.config["DATA_FOLDER"] / filename.replace(".pdf", "")

        if not data_dir.exists():
            return jsonify({"error": "File not found"}), 404

        # Process the PDF asynchronously
        result = await get_pdf_metadata_async(pdf_path, data_dir)

        return jsonify(
            {
                "status": "success",
                "filename": filename,
                "result": result,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/risk_factors/<path:filename>")
async def get_risk_factors(filename):
    """Extract and process risk factors from Item 1A section of 10-K.
    
    Args:
        filename (str): Name of the PDF file to process
        
    Returns:
        flask.Response: JSON response containing:
            - introduction (str): Introductory text of risk factors
            - risk_titles (list): List of risk factor titles
            - risk_descriptions (list): List of risk factor descriptions
            
    Raises:
        404: If risk factors file is not found
        500: If processing fails
    """
    try:
        file_path = (
            current_app.config["DATA_FOLDER"]
            / filename.replace(".pdf", "")
            / "Item 1A.txt"
        )

        # Wait for file to exist
        timeout = 0
        while not file_path.exists():
            if timeout > 10:
                return jsonify({"error": "File not found"}), 404
            await asyncio.sleep(1)
            timeout += 1

        with open(file_path) as f:
            content = f.read()

        # Parse the content
        parsed = parse_risk_factors(content)

        return jsonify(
            {
                "introduction": parsed["introduction"],
                "risk_titles": parsed["risk_titles"],  # Changed from 'summaries'
                "risk_descriptions": parsed[
                    "risk_descriptions"
                ],  # Changed from 'full_text_mapping'
            }
        )

    except Exception as e:
        log.error(f"Error getting risk factors for {filename}: {e}")
        return jsonify({"error": str(e)}), 500


def parse_risk_factors(content):
    """Parse risk factors content into structured sections.
    
    Args:
        content (str): Raw text content from Item 1A
        
    Returns:
        dict: Parsed risk factors containing:
            - introduction (str): Introductory text
            - risk_titles (list): List of risk factor titles
            - risk_descriptions (list): List of full risk factor descriptions
    """
    parts = content.split("Summary of Risk Factors")
    introduction = parts[0].strip()
    introduction = introduction.split("Risk Factors", 1)[1].strip()
    introduction = introduction.replace("*", " ")

    # Get full text section
    full_text = parts[1].split(
        "**Risks Related to Our Limited Operating History, Financial Position and Capital Requirements**",
        1,
    )[1]

    # Get summaries section

    risk_titles = []
    risk_descriptions = []

    split_text = full_text.split("\n")
    boldline = False
    current_title = []
    current_description = []
    for i, line in enumerate(split_text):
        if line.strip()[:2] == "**":
            current_title.append(line)
            boldline = True
        else:
            current_description.append(line)
            boldline = False
        # Check if we're at a boundary between sections
        # Either when we see the next bold line or at the end of the text
        is_last_line = i == len(split_text) - 1
        next_line_is_bold = not is_last_line and split_text[i + 1].strip()[:2] == "**"

        if (not boldline and next_line_is_bold) or is_last_line:
            if current_title:  # Only append if we have a title
                risk_titles.append("\n".join(current_title).replace("*", ""))
                risk_descriptions.append("\n".join(current_description))
                current_title = []
                current_description = []

    return {
        "introduction": introduction,
        "risk_titles": risk_titles,
        "risk_descriptions": risk_descriptions,
    }


@api_bp.route("/section/<path:filename>/<string:item>")
async def get_section(filename, item):
    """Get contents of a specific section from the 10-K filing.
    
    Args:
        filename (str): Name of the PDF file
        item (str): Section identifier (e.g., "Item 1A")
        
    Returns:
        flask.Response: JSON response containing:
            - item (str): Section identifier
            - content (str): Section text content
            - status (str): 'success' or 'error'
            
    Raises:
        404: If section file is not found
        500: If retrieval fails
    """
    try:

        file_path = (
            current_app.config["DATA_FOLDER"]
            / filename.replace(".pdf", "")
            / f"{item}.txt"
        )

        # Wait for file to exist (max 10 seconds)
        timeout = 0
        while not file_path.exists():
            if timeout > 10:
                return jsonify({"error": f"File not found: {item}"}), 404
            await asyncio.sleep(1)
            timeout += 1

        # Read file content
        async with aiofiles.open(file_path) as f:
            content = await f.read()

        return jsonify({"item": item, "content": content, "status": "success"})

    except Exception as e:
        current_app.logger.error(f"Error getting {item} for {filename}: {str(e)}")
        return jsonify({"error": f"Error retrieving {item}: {str(e)}"}), 500
    
@api_bp.route("/finance_tables/<path:filename>")
async def get_financial_tables(filename):
    """Extract and process financial tables from the 10-K filing.
    
    Args:
        filename (str): Name of the PDF file
        
    Returns:
        flask.Response: JSON response containing:
            - status (str): 'success' or 'error'
            - tables (list): List of dictionaries containing:
                - statement (str): Name of financial statement
                - unit (str): Unit of measurement
                - data (list): Table data as list of records
                
    Raises:
        404: If file is not found
        500: If processing fails
        
    Notes:
        Sanitizes data by:
        - Converting numeric values to float
        - Replacing NaN values with empty strings
        - Removing non-ASCII characters from strings
    """
    try:
        file_dir = current_app.config["DATA_FOLDER"] / filename.replace(".pdf", "")
        file_path = (
            file_dir
            / "10k_full_text.txt"
        )

        # Wait for file to exist (max 10 seconds) 
        timeout = 0
        while not file_path.exists():
            if timeout > 10:
                return jsonify({"error": "File not found"}), 404
            await asyncio.sleep(1)
            timeout += 1

        # Parse financial tables
        tables = get_finance_tables(file_dir)

        # Sanitize the data to ensure JSON serialization
        for table in tables:
            for row in table.get('data', []):
                # Convert any special types to basic Python types
                for key, value in row.items():
                    if isinstance(value, (float, int)):
                        # Replace NaN values with empty string or 0
                        if pd.isna(value):  # or math.isnan(value)
                            row[key] = ""  # or 0.0 if you prefer
                        else:
                            row[key] = float(value)
                    elif value is None:
                        row[key] = ""
                    elif isinstance(value, str):
                        # Remove problematic characters and excess whitespace
                        cleaned_value = re.sub(r'[^\x00-\x7F]+', '', value).strip()
                        row[key] = cleaned_value

        return jsonify({
            "status": "success",
            "tables": tables
        })

    except Exception as e:
        current_app.logger.error(f"Error getting financial tables for {filename}: {str(e)}")
        return jsonify({"error": f"Error retrieving financial tables: {str(e)}"}), 500