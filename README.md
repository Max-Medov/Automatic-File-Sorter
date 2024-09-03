Flask File Upload & S3 Storage with DynamoDB
Overview
This project includes three Python scripts that create a web app for file uploads, store the data in an S3 bucket, and manage user information in a DynamoDB table.

1. Flask App (Simple-upload-page.py)
Purpose: A web application where users can upload files along with their name, phone number, and case number. The files are saved with unique names (using a timestamp and UUID) to avoid overwriting existing files. User data, including the file information, is stored in a JSON file on S3 (info/attendance_data.json).
2. S3 File Handler (s3_file_handler.py)
Purpose: Monitors a local directory (/app/uploads) for new files and automatically uploads them to an S3 bucket. Files are categorized by type (e.g., images go to Images/, text files go to Text_files/), ensuring organization in the S3 bucket.
3. DynamoDB Updater (update_dynamodb.py)
Purpose: Periodically checks the JSON file stored on S3 and updates a DynamoDB table with the user data and file paths. The script handles categorization by file type to ensure the correct S3 paths are stored in DynamoDB, allowing for efficient data retrieval and management.
