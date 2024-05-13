from flask import Flask, request, send_from_directory, jsonify, render_template, redirect, url_for
from PIL import Image
import os
from werkzeug.utils import secure_filename
import imghdr  # For image format validation

# Flask app initialization
app = Flask(__name__)

# Configuration variables for folders
UPLOAD_FOLDER = 'uploads/'
RESIZED_FOLDER = 'resized/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESIZED_FOLDER'] = RESIZED_FOLDER

# Allowed image format extensions (set)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check allowed file extension
def allowed_file(filename):
  """
  This function checks if the uploaded filename has a allowed extension.

  Args:
      filename: The filename of the uploaded file.

  Returns:
      bool: True if the extension is allowed, False otherwise.
  """
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to resize and rotate an image
def resize_image(image, size, rotate_degrees):
  """
  This function resizes and rotates an image based on the provided arguments.

  Args:
      image: The PIL Image object to be resized and rotated.
      size: A tuple representing the new width and height of the image.
      rotate_degrees: The number of degrees to rotate the image.

  Returns:
      Image: The resized and rotated image as a PIL Image object.
  """
  image = image.rotate(rotate_degrees, expand=True)
  image = image.resize(size)
  return image

# Route handler for the main page "/"
@app.route('/', methods=['GET', 'POST'])
def upload_file():
  """
  This route handler handles the file upload process.

  Returns:
      render_template: Renders the upload.html template on GET request.
      jsonify: Returns JSON error message on unsuccessful file upload.
      redirect: Redirects to the handle_resize route for successful upload.
  """
  if request.method == 'POST':
    # Check if there's a file part in the request
    if 'file' not in request.files:
      return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # Check if there's a selected file
    if file.filename == '':
      return jsonify({'error': 'No selected file'}), 400

    # Validate file extension
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      return redirect(url_for('handle_resize', filename=filename))

    return jsonify({'error': 'File format not allowed'}), 400

  return render_template('upload.html')

# Route handler for image resize "/resize/<filename>"
@app.route('/resize/<filename>', methods=['GET', 'POST'])
def handle_resize(filename):
  """
  This route handler handles the image resize operation and download.

  Returns:
      render_template: Renders the resize.html template on GET request.
      jsonify: Returns JSON error message on failure.
      send_from_directory: Sends the resized image for download on success.
  """
  upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

  if request.method == 'POST':
    # Get user input for resize parameters
    size = tuple(int(x) for x in request.form.get('size', '100,100').split(','))
    rotate_degrees = int(request.form.get('rotate', 0))
    output_folder = request.form.get('output_folder', RESIZED_FOLDER)  # Default output folder

    # Check if uploaded file exists
    if os.path.isfile(upload_path):
      try:
        # Open the image and perform resize/rotate operation
        with Image.open(upload_path) as image:
          resized_image = resize_image(image, size, rotate_degrees)

        # Create output folder if it doesn't exist
        os.makedirs(os.path.dirname(resized_path), exist_ok=True)
        resized_
