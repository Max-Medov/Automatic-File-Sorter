# Flask App Code

import os
import json
import boto3
from flask import Flask, request, jsonify
from datetime import datetime

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
    file_path = None
    if file:
        # Validate file extension
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'txt', 'pdf'}
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        if file_extension in allowed_extensions:
            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)
        else:
            return jsonify({'error': 'Invalid file type. Only image, text, and PDF files are allowed.'}), 400

    now = datetime.now().strftime('%Y-%m-%d')
    json_data = {
        'date': now,
        'entries': [{
            'name': name,
            'phone': phone,
            'case_number': case_number,
            'file': file_path
        }]
    }

    # Upload JSON data to S3
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key='info/attendance_data.json', Body=json.dumps(json_data))

    return jsonify({'message': 'Data stored successfully.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
