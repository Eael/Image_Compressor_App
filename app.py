from flask import Flask, request, send_from_directory, jsonify, render_template, redirect, url_for
from PIL import Image
import os
from werkzeug.utils import secure_filename
import imghdr  # For image format validation

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
RESIZED_FOLDER = 'resized/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESIZED_FOLDER'] = RESIZED_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed image formats

def allowed_file(filename):
    """Check if the uploaded file is an allowed image format"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image, size, rotate_degrees):
    """Resize and rotate the input image"""
    image = image.rotate(rotate_degrees, expand=True)
    image = image.resize(size)
    return image

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """Upload a file and save it to the uploads folder"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('handle_resize', filename=filename))

        return jsonify({'error': 'File format not allowed'}), 400

    return render_template('upload.html')

@app.route('/resize/<filename>', methods=['GET', 'POST'])
def handle_resize(filename):
    """Handle the resize operation and download the specified image"""
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if request.method == 'POST':
        size = tuple(int(x) for x in request.form.get('size', '100,100').split(','))
        rotate_degrees = int(request.form.get('rotate', 0))
        output_folder = request.form.get('output_folder')

        if os.path.isfile(upload_path):
            try:
                with Image.open(upload_path) as image:
                    resized_image = resize_image(image, size, rotate_degrees)
                    resized_path = os.path.join(output_folder, filename)
                    os.makedirs(os.path.dirname(resized_path), exist_ok=True)
                    resized_image.save(resized_path)
                return send_from_directory(os.path.dirname(resized_path), os.path.basename(resized_path), as_attachment=True)
            except IOError:
                return jsonify({'error': 'Error opening or processing the image'}), 500
        else:
            return jsonify({'error': 'File not found'}), 404

    return render_template('resize.html', filename=filename)

@app.route('/list_images', methods=['GET'])
def list_images():
    """List all uploaded and resized images"""
    uploads = os.listdir(app.config['UPLOAD_FOLDER'])
    resized = os.listdir(app.config['RESIZED_FOLDER'])
    return jsonify({'uploads': uploads, 'resized': resized}), 200

if __name__ == '__main__':
    # Create the uploads and resized folders if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESIZED_FOLDER'], exist_ok=True)
    app.run(debug=True)
