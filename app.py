from flask import Flask, render_template, request, jsonify, send_file
import os
import subprocess
import fitz  # PyMuPDF
from PIL import Image
import tempfile
import shutil
from werkzeug.utils import secure_filename
import time
import logging
import zipfile

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename, file_type):
    """Check if the file type is allowed based on the selected file type."""
    video_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    pdf_extensions = {'.pdf'}
    
    ext = os.path.splitext(filename.lower())[1]
    
    if file_type == 'Videos':
        return ext in video_extensions
    elif file_type == 'Images':
        return ext in image_extensions
    elif file_type == 'PDFs':
        return ext in pdf_extensions
    else:  # All Files
        return ext in video_extensions | image_extensions | pdf_extensions

def compress_file(file_path, quality, file_type):
    """Compress a file based on its type and quality setting."""
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename.lower())[1]
    output_path = os.path.join(os.path.dirname(file_path), f'compressed_{filename}')
    
    try:
        logger.debug(f"Starting compression of {filename} with quality {quality}")
        
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
            # Compress image
            logger.debug(f"Compressing image: {filename}")
            with Image.open(file_path) as img:
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                img.save(output_path, quality=quality, optimize=True)
            logger.debug(f"Image compression complete: {output_path}")
                
        elif ext in {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'}:
            # Compress video using FFmpeg with optimized settings
            logger.debug(f"Compressing video: {filename}")
            crf = int(51 - (quality * 0.51))  # Convert quality (0-100) to CRF (51-0)
            
            # Optimized FFmpeg settings for faster compression
            ffmpeg_cmd = [
                'ffmpeg', '-i', file_path,
                '-c:v', 'libx264',
                '-preset', 'veryfast',  # Faster encoding
                '-crf', str(crf),
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',  # Enable fast start for web playback
                '-y',  # Overwrite output file if it exists
                output_path
            ]
            logger.debug(f"Running FFmpeg command: {' '.join(ffmpeg_cmd)}")
            
            # Run FFmpeg with timeout
            try:
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=300  # 5-minute timeout
                )
                logger.debug(f"FFmpeg output: {result.stdout}")
                if result.stderr:
                    logger.debug(f"FFmpeg errors: {result.stderr}")
                logger.debug(f"Video compression complete: {output_path}")
            except subprocess.TimeoutExpired:
                raise Exception("Video compression timed out after 5 minutes")
            
        elif ext == '.pdf':
            # Compress PDF
            logger.debug(f"Compressing PDF: {filename}")
            doc = fitz.open(file_path)
            for page in doc:
                page.clean_contents()
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            logger.debug(f"PDF compression complete: {output_path}")
            
        if not os.path.exists(output_path):
            raise Exception(f"Output file was not created: {output_path}")
            
        return output_path
    except Exception as e:
        logger.error(f"Error compressing {filename}: {str(e)}")
        raise Exception(f"Error compressing {filename}: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress():
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files[]')
        quality = int(request.form.get('quality', 80))
        file_type = request.form.get('fileType', 'All Files')
        
        logger.debug(f"Received compression request: {len(files)} files, quality={quality}, type={file_type}")
        
        if not files:
            return jsonify({'error': 'No files selected'}), 400
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            compressed_files = []
            total_files = len(files)
            processed_files = 0
            
            for file in files:
                if file.filename == '':
                    continue
                    
                if not allowed_file(file.filename, file_type):
                    logger.warning(f"Skipping unsupported file: {file.filename}")
                    continue
                    
                # Save uploaded file
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                logger.debug(f"Saved uploaded file: {file_path}")
                
                try:
                    # Compress file
                    compressed_path = compress_file(file_path, quality, file_type)
                    compressed_files.append(compressed_path)
                    processed_files += 1
                    logger.debug(f"Successfully compressed: {filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to compress {filename}: {str(e)}")
                    return jsonify({'error': str(e)}), 500
            
            if not compressed_files:
                return jsonify({'error': 'No valid files to compress'}), 400
            
            # Create ZIP file of compressed files
            zip_path = os.path.join(temp_dir, 'compressed_files.zip')
            logger.debug(f"Creating ZIP file: {zip_path}")
            
            try:
                # Create a new ZIP file
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in compressed_files:
                        # Get just the filename without the path
                        filename = os.path.basename(file_path)
                        # Add file to ZIP
                        zipf.write(file_path, filename)
                        logger.debug(f"Added {filename} to ZIP")
                
                if not os.path.exists(zip_path):
                    raise Exception("Failed to create ZIP file")
                
                logger.debug("ZIP file created successfully")
                
                # Get file size for logging
                zip_size = os.path.getsize(zip_path)
                logger.debug(f"ZIP file size: {zip_size / 1024 / 1024:.2f} MB")
                
                return send_file(
                    zip_path,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name='compressed_files.zip'
                )
                
            except Exception as e:
                logger.error(f"Error creating ZIP file: {str(e)}")
                return jsonify({'error': f"Failed to create ZIP file: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error in compress route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/merge-pdf', methods=['POST'])
def merge_pdf():
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files[]')
        logger.debug(f"Received PDF merge request: {len(files)} files")
        
        if not files:
            return jsonify({'error': 'No files selected'}), 400
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_files = []
            total_files = len(files)
            processed_files = 0
            
            for file in files:
                if file.filename == '':
                    continue
                    
                if not file.filename.lower().endswith('.pdf'):
                    logger.warning(f"Skipping non-PDF file: {file.filename}")
                    continue
                    
                # Save uploaded file
                filename = secure_filename(file.filename)
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                pdf_files.append(file_path)
                processed_files += 1
                logger.debug(f"Added PDF to merge: {filename}")
            
            if not pdf_files:
                return jsonify({'error': 'No valid PDF files to merge'}), 400
            
            # Merge PDFs
            output_path = os.path.join(temp_dir, 'merged.pdf')
            logger.debug("Starting PDF merge")
            merged_pdf = fitz.open()
            
            for pdf_file in pdf_files:
                doc = fitz.open(pdf_file)
                merged_pdf.insert_pdf(doc)
                doc.close()
            
            merged_pdf.save(output_path)
            merged_pdf.close()
            logger.debug(f"PDF merge complete: {output_path}")
            
            if not os.path.exists(output_path):
                raise Exception("Failed to create merged PDF file")
            
            return send_file(
                output_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='merged.pdf'
            )
            
    except Exception as e:
        logger.error(f"Error in merge_pdf route: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use environment variable for port in production
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 