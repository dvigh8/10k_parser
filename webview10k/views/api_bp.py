from flask import Blueprint, jsonify, current_app
from pathlib import Path
import asyncio
from ..utils.pdf_processor import process_pdf_async  # We'll create this next

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/process/<string:filename>', methods=['POST'])
async def process_pdf(filename: str):
    """Process a PDF file asynchronously"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        pdf_path = upload_folder / filename
        
        if not pdf_path.exists():
            return jsonify({'error': 'File not found'}), 404
            
        # Process the PDF asynchronously
        result = await process_pdf_async(pdf_path)
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500