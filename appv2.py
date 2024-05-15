from flask import Flask, request, send_from_directory, jsonify, render_template, redirect, url_for
# Import necessary Flask functions and modules

from PIL import Image
# Import the Image module from the Pillow library for image processing

import os
# Import the os module for interacting with the operating system

from werkzeug.utils import secure_filename
# Import the secure_filename function from Werkzeug for securing file names

import imghdr  # For image format validation
# Import the imghdr module for validating image file formats

app = Flask(__name__)
# Create a Flask application instance

UPLOAD_FOLDER = 'uploads/'
RESIZED_FOLDER = 'resized/'
# Define the paths for the upload and resized folders

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESIZED_FOLDER'] = RESIZED_FOLDER
# Configure the Flask app with the upload and resized folder paths

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed image formats
# Define a set of allowed image file extensions

def allowed_file(filename):
    """
    Check if the uploaded file is an allowed image format.

    Args:
        filename (str): The name of the uploaded file.

    Returns:
        bool: True if the file extension is allowed, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image, size, rotate_degrees):
    """
    Resize and rotate the input image.

    Args:
        image (PIL.Image.Image): The input image object.
        size (tuple): The desired size for the resized image.
        rotate_degrees (int): The number of degrees to rotate the image.

    Returns:
        PIL.Image.Image: The resized and rotated image object.
    """
    image = image.rotate(rotate_degrees, expand=True)
    image = image.resize(size)
    return image

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """
    Handle the file upload process.

    If the request method is POST, it checks if a file is uploaded, validates the file format,
    saves the file to the uploads folder, and redirects to the resize page.
    If the request method is GET, it renders the upload.html template.

    Returns:
        A JSON response with an error message if the file is not uploaded or the format is not allowed.
        A redirect to the resize page if the file is uploaded and the format is allowed.
        The upload.html template if the request method is GET.
    """
    if request.method == 'POST':
        # Check if a file is uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        file = request.files['file']

        # Check if the file name is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check if the file format is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('handle_resize', filename=filename))

        return jsonify({'error': 'File format not allowed'}), 400

    return render_template('upload.html')

@app.route('/resize/<filename>', methods=['GET', 'POST'])
def handle_resize(filename):
    """
    Handle the image resizing and rotation operation.

    If the request method is POST, it resizes and rotates the specified image based on the provided parameters
    and saves the resized image to the specified output folder. If the output folder is not specified,
    it saves the resized image to the default resized folder. It then sends the resized image as an attachment.
    If the request method is GET, it renders the resize.html template with the filename.

    Args:
        filename (str): The name of the uploaded file.

    Returns:
        A JSON response with an error message if the file is not found or an error occurs during processing.
        The resized image file as an attachment if the resizing operation is successful.
        The resize.html template with the filename if the request method is GET.
    """
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
    """
    List all uploaded and resized images.

    Returns:
        A JSON response containing a list of uploaded and resized image filenames.
    """
    uploads = os.listdir(app.config['UPLOAD_FOLDER'])
    resized = os.listdir(app.config['RESIZED_FOLDER'])
    return jsonify({'uploads': uploads, 'resized': resized}), 200

if __name__ == '__main__':
    # Create the uploads and resized folders if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESIZED_FOLDER'], exist_ok=True)

    app.run(debug=False)
