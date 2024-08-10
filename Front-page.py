from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

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
    <head>
        <title>Automatic File Sorter</title>
    </head>
    <body>
        <h1>Automatic File Sorter</h1>
        <form id="attendanceForm" method="post" action="/submit" enctype="multipart/form-data">
            <label for="name">Name:</label>
            <input type="text" id="name" name="name" required><br><br>
            <label for="phone">Phone Number:</label>
            <input type="text" id="phone" name="phone" required><br><br>
            <label for="file">Upload a File:</label>
            <input type="file" id="file" name="file" accept=".jpg, .jpeg, .png, .gif, .txt, .pdf"><br><br>
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    '''

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    phone = request.form.get('phone')
    file = request.files.get('file')
    now = datetime.now().strftime('%Y-%m-%d')

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

    # Load existing data for the date if it exists
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as f:
            existing_data = json.load(f)
        if not isinstance(existing_data, dict) or 'date' not in existing_data or existing_data['date'] != now:
            existing_data = {
                'date': now,
                'entries': []
            }
    else:
        existing_data = {
            'date': now,
            'entries': []
        }

    # Append new entry data
    entry_data = {
        'name': name,
        'phone': phone,
        'file': file_path if file else None
    }
    existing_data['entries'].append(entry_data)

    # Store the updated data back in the local file
    with open(json_file_path, 'w') as f:
        json.dump(existing_data, f)

    return jsonify({'message': 'Data stored successfully.'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
