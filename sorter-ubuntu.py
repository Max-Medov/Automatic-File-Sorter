import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define source and destination folders
UPLOAD_FOLDER = '/app/uploads'
TEXT_FILES_FOLDER = '/app/Text_files'
IMAGES_FOLDER = '/app/Images'

# Create folders if they don't exist
os.makedirs(TEXT_FILES_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)

class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            self.process(event.src_path)
    
    def process(self, file_path):
        file_extension = file_path.rsplit('.', 1)[-1].lower()
        if file_extension in {'jpg', 'jpeg', 'png', 'gif'}:
            shutil.move(file_path, os.path.join(IMAGES_FOLDER, os.path.basename(file_path)))
        elif file_extension in {'txt', 'pdf'}:
            shutil.move(file_path, os.path.join(TEXT_FILES_FOLDER, os.path.basename(file_path)))
        else:
            print(f"Unsupported file type: {file_path}")

# Set up the observer
observer = Observer()
event_handler = FileHandler()
observer.schedule(event_handler, path=UPLOAD_FOLDER, recursive=False)
observer.start()

print(f"Monitoring folder {UPLOAD_FOLDER} for new files...")

try:
    while True:
        pass  # Keep the script running
except KeyboardInterrupt:
    observer.stop()
observer.join()
