import boto3
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch DynamoDB table name from environment variable
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME')

if not DYNAMODB_TABLE_NAME:
    raise ValueError("DYNAMODB_TABLE_NAME environment variable is not set.")

# Set the AWS region
AWS_REGION = "us-east-1"

# Initialize DynamoDB and S3 clients with the region
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
s3_client = boto3.client('s3', region_name=AWS_REGION)

# Fetch S3 bucket name from environment variable
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is not set.")

# Reference the DynamoDB table
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def update_dynamodb(case_number, user_name, phone_number, s3_path):
    """Updates the DynamoDB table by appending the new file details to an existing case number if the file doesn't already exist."""
    try:
        # Fetch the current item from DynamoDB to check if the file already exists
        response = table.get_item(Key={'CaseNumber': case_number})
        if 'Item' in response:
            existing_files = response['Item'].get('Files', [])
        else:
            existing_files = []

        # Check if the file already exists in the Files list
        file_exists = any(file['FilePath'] == s3_path for file in existing_files)

        if not file_exists:
            # Only append the new file if it doesn't exist already
            response = table.update_item(
                Key={'CaseNumber': case_number},
                UpdateExpression="SET #un = :un, #pn = :pn, Files = list_append(if_not_exists(Files, :empty_list), :file)",
                ExpressionAttributeNames={
                    '#un': 'UserName',
                    '#pn': 'PhoneNumber',
                },
                ExpressionAttributeValues={
                    ':un': user_name,
                    ':pn': phone_number,
                    ':file': [{
                        'FilePath': s3_path,
                        'UploadTimestamp': datetime.utcnow().isoformat()
                    }],
                    ':empty_list': []
                },
                ReturnValues="UPDATED_NEW"
            )
            print(f"Successfully updated DynamoDB for case number {case_number}")
        else:
            print(f"File {s3_path} already exists for case number {case_number}, skipping update.")

    except Exception as e:
        print(f"Error updating DynamoDB: {e}")


def process_json_and_update_dynamodb():
    """Process the JSON data from S3 and update DynamoDB."""
    try:
        # Check if the JSON file exists in S3
        json_key = 'info/attendance_data.json'
        try:
            s3_response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=json_key)
            json_data = json.loads(s3_response['Body'].read().decode('utf-8'))
        except s3_client.exceptions.NoSuchKey:
            print(f"JSON file {json_key} does not exist in S3.")
            return  # Exit if the JSON file doesn't exist

        # Loop through each case number and update DynamoDB with the correct S3 paths
        for case_number, records in json_data.items():
            for record in records:
                user_name = record['name']
                phone_number = record['phone']
                file_name = record['file']

                # Determine the correct S3 path after sorting
                if file_name:
                    file_extension = file_name.rsplit('.', 1)[-1].lower()
                    if file_extension in {'jpg', 'jpeg', 'png', 'gif'}:
                        s3_path = f"s3://{S3_BUCKET_NAME}/Images/{file_name}"
                    elif file_extension in {'txt', 'pdf'}:
                        s3_path = f"s3://{S3_BUCKET_NAME}/Text_files/{file_name}"
                    else:
                        print(f"Unsupported file type for {file_name}, skipping...")
                        continue

                    # Update DynamoDB with the correct path
                    update_dynamodb(case_number, user_name, phone_number, s3_path)

    except Exception as e:
        print(f"Error processing JSON and updating DynamoDB: {e}")

def monitor_json_file():
    """Continuously monitor the JSON file for changes."""
    last_modified_time = None
    json_key = 'info/attendance_data.json'

    while True:
        try:
            # Get the current last modified time of the JSON file
            response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=json_key)
            current_modified_time = response['LastModified']

            # Check if the file has been updated since the last check
            if last_modified_time is None or current_modified_time != last_modified_time:
                print(f"File {json_key} has been updated, processing...")
                process_json_and_update_dynamodb()
                last_modified_time = current_modified_time

            time.sleep(30)  # Wait 30 seconds before checking again

        except Exception as e:
            print(f"Error monitoring JSON file: {e}")
            time.sleep(60)  # Wait 60 seconds before retrying

if __name__ == '__main__':
    monitor_json_file()
