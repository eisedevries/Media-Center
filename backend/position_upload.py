import os
from pathlib import Path
import base64
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def get_auth_header():
    username = os.getenv('WEBDAV_USERNAME')
    password = os.getenv('WEBDAV_PASSWORD')
    if not username or not password:
        raise ValueError("WebDAV credentials not found in environment variables")
    
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"

def get_latest_watch_later_file(max_age_seconds=30):
    # Get path to watch_later directory
    watch_later_path = Path('portable_config/watch_later')
    
    # Check if directory exists
    if not watch_later_path.exists():
        return None, "Watch later directory not found"
    
    # Get all files in the directory as a list (not an iterator)
    try:
        files = list(watch_later_path.glob('*'))
        
        if not files:
            return None, "No files found in watch_later directory"
        
        # Find the latest file by modification time
        latest_file = max(files, key=lambda x: x.stat().st_mtime)
        
        # Check if file was modified recently
        mtime = latest_file.stat().st_mtime
        if time.time() - mtime > max_age_seconds:
            return None, f"No files modified in the last {max_age_seconds} seconds found"
            
        return latest_file, None
    except Exception as e:
        return None, f"Error getting watch_later files: {str(e)}"

def upload_to_webdav(file_path):
    base_webdav_url = os.getenv('WEBDAV_URL')
    auth_header = get_auth_header()
    
    # Extract the base part of the URL (before any additional folders)
    webdav_base_parts = base_webdav_url.split('/remote.php/webdav/')
    if len(webdav_base_parts) > 1:
        # If we found the pattern, use everything before it plus '/remote.php/webdav/'
        webdav_base = webdav_base_parts[0] + '/remote.php/webdav'
    else:
        # If pattern not found, use the URL as is
        webdav_base = base_webdav_url
    
    # Read file content
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # Get just the filename
    filename = os.path.basename(str(file_path))
    
    # Construct WebDAV path
    webdav_path = f"{webdav_base}/watch_later/{filename}"
    
    print(f"Uploading position file to {webdav_path}")
    
    # Send file to WebDAV
    response = requests.put(
        webdav_path,
        headers={
            'Authorization': auth_header,
            'Content-Type': 'application/octet-stream'
        },
        data=content
    )
    
    if response.status_code in [200, 201, 204]:
        return True
    else:
        print(f"Upload failed with status code {response.status_code}")
        return False

if __name__ == '__main__':
    latest_file, error = get_latest_watch_later_file()
    if error:
        if "No recently modified files" not in error:  # Only print actual errors
            print(f"Error: {error}")
    elif upload_to_webdav(latest_file):
        pass  # Success - stay quiet
    else:
        print("Failed to upload to WebDAV")  # Only print on failure