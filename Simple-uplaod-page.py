# Flask App Code

import os
import json
import boto3
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

S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
s3_client = boto3.client('s3')

# Define the local path for storing JSON data and uploaded files
json_file_path = '/app/info/attendance_data.json'
upload_folder = '/app/uploads'

os.makedirs(upload_folder, exist_ok=True)
os.makedirs(os.path.dirname(json_file_path), exist_ok=True)

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
            <input type="text" name="case_number" placeholder="Case Number" pattern="\d{6}" required><br>
            <input type="file" name="file"><br>
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    '''

@app.route('/submit', methods=['POST'])
def submit():
    name, phone, case_number = request.form['name'], request.form['phone'], request.form['case_number']
    file = request.files.get('file')
    file_path = None

    # Handle file upload
    if file:
        # Validate file extension
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'txt', 'pdf', 'doc', 'docx'}
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        if file_extension in allowed_extensions:
            # Generate a unique filename using UUID and timestamp
            unique_suffix = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}"
            unique_filename = f"{file.filename.rsplit('.', 1)[0]}_{unique_suffix}.{file_extension}"

            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)
        else:
            return jsonify({'error': 'Invalid file type. Only image, text, PDF, and Word files are allowed.'}), 400

    # Load existing data from S3 or create an empty structure if it doesn't exist
    try:
        s3_response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key='info/attendance_data.json')
        json_data = json.loads(s3_response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        json_data = {}  # Initialize an empty dictionary if the file doesn't exist

    # Add or append to the existing list under the case number
    if case_number not in json_data:
        json_data[case_number] = []

    json_data[case_number].append({
        'name': name,
        'phone': phone,
        'file': file.filename
    })

    # Upload the updated JSON data back to S3
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key='info/attendance_data.json', Body=json.dumps(json_data))

    return jsonify({'message': 'Data stored successfully.'})



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
