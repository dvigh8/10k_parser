from flask import Blueprint, render_template, request, current_app, redirect, url_for
from werkzeug.utils import secure_filename

main_bp = Blueprint("main", __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route("/", methods=['GET', 'POST'])
def index():
    """
    Landing page route with file upload functionality.
    Accessible to both authenticated and non-authenticated users.
    """
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            upload_folder = current_app.config['UPLOAD_FOLDER']
            file.save(upload_folder / filename)
            return redirect(url_for('main.dashboard', filename=filename))
    return render_template("index.html")


@main_bp.route("/dashboard/<string:filename>")
def dashboard(filename: str):
    """
    Dashboard view that will make async calls to the API
    """
    return render_template(
        "dashboard.html", 
        filename=filename,
        api_url=url_for('api.process_pdf', filename=filename)
    )
    
    
@main_bp.route("/uploads")
def uploads():
    """
    Display all uploaded files in the uploads directory.
    """
    upload_folder = current_app.config['UPLOAD_FOLDER']
    files = [f.name for f in upload_folder.iterdir() if f.is_file() and allowed_file(f.name)]
    return render_template("uploads.html", files=files)