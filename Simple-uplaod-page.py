import os
import json
import boto3
import uuid
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch the S3 bucket name from environment variable
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is not set.")

app = Flask(__name__)

s3_client = boto3.client('s3')

# Define the local path for storing uploaded files
upload_folder = '/app/uploads'
os.makedirs(upload_folder, exist_ok=True)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <body>
        <h1>File Upload</h1>
        <form method="post" action="/submit" enctype="multipart/form-data">
            <input type="text" name="name" placeholder="Name" required><br>
            <input type="text" name="phone" placeholder="Phone" required><br>
            <input type="text" name="serial_number" placeholder="Serial Number" pattern="\\d{6}" required><br>
            <select name="department" required>
                <option value="">Select Department</option>
                <option value="R&D">R&D</option>
                <option value="DevOps">DevOps</option>
                <option value="IT">IT</option>
            </select><br>
            <input type="file" name="file"><br>
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    '''

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    phone = request.form['phone']
    serial_number = request.form['serial_number']
    department = request.form['department']
    file = request.files.get('file')
    file_path = None

    # Handle file upload
    if file:
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'txt', 'pdf', 'doc', 'docx'}
        file_extension = file.filename.rsplit('.', 1)[-1].lower()

        if file_extension in allowed_extensions:
            unique_suffix = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}"
            unique_filename = f"{file.filename.rsplit('.', 1)[0]}_{unique_suffix}.{file_extension}"
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)

            # Upload the file to the selected department folder
            s3_file_key = f"{department}/{unique_filename}"
            s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_file_key)
        else:
            return jsonify({'error': 'Invalid file type. Only image, text, PDF, and Word files are allowed.'}), 400
    else:
        unique_filename = None  # Handle case with no file uploaded

    # Always load and update JSON in the IT folder
    json_key = "IT/attendance_data.json"
    try:
        s3_response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=json_key)
        json_data = json.loads(s3_response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        json_data = {}

    if serial_number not in json_data:
        json_data[serial_number] = []

    json_data[serial_number].append({
        'name': name,
        'phone': phone,
        'file': unique_filename,
        'department': department,
        'timestamp': datetime.utcnow().isoformat()
    })

    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=json_key, Body=json.dumps(json_data))

    return jsonify({'message': 'Data stored successfully.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
