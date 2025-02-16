from flask import Blueprint, render_template, request, current_app, redirect, url_for
from werkzeug.utils import secure_filename
from ..utils.pdf_processor import get_pdf_info, process_pdf_async
import asyncio
from ..config import log

main_bp = Blueprint("main", __name__)


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension.
    
    Args:
        filename (str): Name of the file to check
        
    Returns:
        bool: True if file extension is allowed (.pdf), False otherwise
        
    Notes:
        Allowed extensions are defined in ALLOWED_EXTENSIONS set
    """
    ALLOWED_EXTENSIONS = {"pdf"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@main_bp.route("/", methods=["GET", "POST"])
async def index():
    """Handle the landing page and file upload functionality.
    
    Methods:
        GET: Display the upload form
        POST: Handle file upload
        
    Returns:
        GET: Rendered index.html template
        POST: 
            - Redirect to dashboard if upload successful
            - Error message (400) if upload fails
            
    Notes:
        - Saves uploaded file to UPLOAD_FOLDER
        - Creates directory in DATA_FOLDER for processing
        - Initiates async processing of PDF file
    """
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part", 400
        file = request.files["file"]
        if file.filename == "":
            return "No selected file", 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Save uploaded file
            upload_folder = current_app.config["UPLOAD_FOLDER"]
            pdf_path = upload_folder / filename
            file.save(pdf_path)

            data_dir = current_app.config["DATA_FOLDER"] / filename.replace(".pdf", "")

            # Generate index
            get_pdf_info(pdf_path, data_dir)

            # Start background processing
            asyncio.create_task(process_pdf_async(pdf_path, data_dir))
            log.info(f"Saved uploaded file to {pdf_path} and started processing")
            return redirect(url_for("main.dashboard", filename=filename))
    return render_template("index.html")


@main_bp.route("/dashboard/<string:filename>")
def dashboard(filename: str):
    """Display the dashboard view for analyzing a specific 10-K filing.
    
    Args:
        filename (str): Name of the uploaded PDF file
        
    Returns:
        str: Rendered dashboard.html template with:
            - filename: Name of current file
            - api_url: URL for processing status endpoint
            
    Notes:
        Dashboard makes async API calls to fetch:
        - Risk factors
        - Financial tables
        - Section content
    """
    return render_template(
        "dashboard.html",
        filename=filename,
        api_url=url_for("api.process_pdf", filename=filename),
    )


@main_bp.route("/uploads")
def uploads():
    """List all previously uploaded PDF files.
    
    Returns:
        str: Rendered uploads.html template containing:
            - files: List of uploaded PDF filenames
            
    Notes:
        Only shows files with allowed extensions from UPLOAD_FOLDER
    """
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    files = [
        f.name for f in upload_folder.iterdir() if f.is_file() and allowed_file(f.name)
    ]
    return render_template("uploads.html", files=files)
