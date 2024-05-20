from flask import Flask, request, send_from_directory, jsonify, render_template, redirect, url_for, flash
from PIL import Image, ImageOps
import os
from werkzeug.utils import secure_filename
from celery import Celery
import logging

app = Flask(__name__, static_url_path='/static', static_folder='static')

UPLOAD_FOLDER = 'uploads/'
RESIZED_FOLDER = 'resized/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESIZED_FOLDER'] = RESIZED_FOLDER
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed image formats

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)

# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def allowed_file(filename):
    """Check if the uploaded file is an allowed image format"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image, size, rotate_degrees, maintain_aspect_ratio=False, crop=False, watermark=None):
    """Resize, rotate, and apply advanced options to the input image"""
    image = image.rotate(rotate_degrees, expand=True)
    if maintain_aspect_ratio:
        width, height = image.size
        aspect_ratio = width / height
        target_width, target_height = size
        if aspect_ratio > 1:
            new_height = int(target_width / aspect_ratio)
            resized_image = image.resize((target_width, new_height), Image.LANCZOS)
        else:
            new_width = int(target_height * aspect_ratio)
            resized_image = image.resize((new_width, target_height), Image.LANCZOS)
    else:
        resized_image = image.resize(size, Image.LANCZOS)
    if crop:
        width, height = resized_image.size
        target_width, target_height = size
        left = (width - target_width) // 2
        top = (height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        resized_image = resized_image.crop((left, top, right, bottom))
    if watermark:
        watermark_width, watermark_height = watermark.size
        width, height = resized_image.size
        position = (width - watermark_width - 10, height - watermark_height - 10)
        resized_image.paste(watermark, position, mask=watermark)
    return resized_image

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    """Upload a file and save it to the uploads folder"""
    if request.method == 'POST':
        if 'file' not in request.files:
            logging.warning('No file part in request')
            return jsonify({'error': 'No file part'}), 400
        files = request.files.getlist('file')
        if not files:
            logging.warning('No selected file')
            return jsonify({'error': 'No selected file'}), 400
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logging.info(f'File uploaded: {filename}')
        return redirect(url_for('batch_processing'))
    return render_template('upload.html')

@app.route('/batch_processing', methods=['GET', 'POST'])
def batch_processing():
    watermark_path = None  # Initialize watermark_path outside the conditional block
    if request.method == 'POST':
        size = tuple(int(x) for x in request.form.get('size', '100,100').split(','))
        rotate_degrees = int(request.form.get('rotate', 0))
        output_folder = request.form.get('output_folder', 'resized')
        maintain_aspect_ratio = 'maintain_aspect_ratio' in request.form
        crop = 'crop' in request.form
        watermark_file = request.files.get('watermark')
        if watermark_file and allowed_file(watermark_file.filename):
            watermark_path = os.path.join(app.config['UPLOAD_FOLDER'], 'watermark.png')
            watermark_file.save(watermark_path)
            watermark = Image.open(watermark_path)
        else:
            watermark = None
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_file(filename):
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                resize_image_task.delay(upload_path, size, rotate_degrees, maintain_aspect_ratio, crop, output_folder, watermark_path)
                logging.info(f'Batch resize task added for: {upload_path}')
        return jsonify({'message': 'Batch image processing started'}), 200
    return render_template('batch_resize.html')



@celery.task
def resize_image_task(upload_path, size, rotate_degrees, maintain_aspect_ratio, crop, output_folder, watermark_path):
    try:
        with Image.open(upload_path) as image:
            watermark = None
            if watermark_path:
                watermark = Image.open(watermark_path)
            resized_image = resize_image(image, size, rotate_degrees, maintain_aspect_ratio, crop, watermark)
            resized_filename = os.path.basename(upload_path)
            resized_path = os.path.join(output_folder, resized_filename)
            os.makedirs(os.path.dirname(resized_path), exist_ok=True)
            resized_image.save(resized_path)
            logging.info(f'Image saved to: {resized_path}')
    except Exception as e:
        logging.error(f'Error processing image {upload_path}: {str(e)}', exc_info=True)



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
                resize_image_task.delay(upload_path, size, rotate_degrees, False, False, output_folder, None)
                logging.info(f'Resize task added for: {upload_path}')
                return jsonify({'message': 'Image is being processed'}), 200
            except IOError:
                logging.error('Error opening or processing the image', exc_info=True)
                return jsonify({'error': 'Error opening or processing the image'}), 500
        else:
            logging.warning(f'File not found: {upload_path}')
            return jsonify({'error': 'File not found'}), 404
    return render_template('resize.html', filename=filename)

@app.route('/list_images', methods=['GET'])
def list_images():
    """List all uploaded and resized images"""
    uploads = os.listdir(app.config['UPLOAD_FOLDER'])
    resized = os.listdir(app.config['RESIZED_FOLDER'])
    return jsonify({'uploads': uploads, 'resized': resized}), 200

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESIZED_FOLDER'], exist_ok=True)
    app.run(debug=True)

