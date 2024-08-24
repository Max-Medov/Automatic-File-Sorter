import os
import boto3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Fetch the S3 bucket name from environment variable
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is not set.")

# Initialize S3 client
s3_client = boto3.client('s3')

# Define the local folder to monitor for new files
UPLOAD_FOLDER = '/app/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class S3FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            self.upload_to_s3(event.src_path)

    def upload_to_s3(self, file_path):
        """Uploads the given file to the specified S3 bucket."""
        file_name = os.path.basename(file_path)
        file_extension = file_name.rsplit('.', 1)[-1].lower()
        
        # Determine S3 folder based on file type
        if file_extension in {'jpg', 'jpeg', 'png', 'gif'}:
            s3_key = f"Images/{file_name}"
        elif file_extension in {'txt', 'pdf'}:
            s3_key = f"Text_files/{file_name}"
        else:
            print(f"Unsupported file type: {file_path}")
            return

        try:
            s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
            print(f"Uploaded {file_path} to s3://{S3_BUCKET_NAME}/{s3_key}")
            os.remove(file_path)  # Clean up local file after uploading
        except Exception as e:
            print(f"Failed to upload {file_path} to S3: {e}")

# Set up the observer to monitor the upload folder
observer = Observer()
event_handler = S3FileHandler()
observer.schedule(event_handler, path=UPLOAD_FOLDER, recursive=False)
observer.start()

print(f"Monitoring folder {UPLOAD_FOLDER} for new files...")

try:
    while True:
        pass  # Keep the script running
except KeyboardInterrupt:
    observer.stop()
observer.join()
