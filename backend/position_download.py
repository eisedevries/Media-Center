import os
import hashlib
from pathlib import Path
import base64
import requests
from dotenv import load_dotenv
import sys

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

def download_from_webdav(url):
    # Calculate hash and setup paths
    file_hash = hashlib.md5(url.encode()).hexdigest().upper()
    watch_later_path = Path('portable_config/watch_later')
    watch_later_path.mkdir(exist_ok=True)
    
    # Get the base WebDAV URL (everything up to /remote.php/webdav/)
    base_webdav_url = os.getenv('WEBDAV_URL')
    # Extract the base part of the URL (before any additional folders)
    webdav_base_parts = base_webdav_url.split('/remote.php/webdav/')
    if len(webdav_base_parts) > 1:
        # If we found the pattern, use everything before it plus '/remote.php/webdav/'
        webdav_base = webdav_base_parts[0] + '/remote.php/webdav'
    else:
        # If pattern not found, use the URL as is
        webdav_base = base_webdav_url
    
    # Construct path to watch_later file
    webdav_path = f"{webdav_base}/watch_later/{file_hash}"
    
    response = requests.get(webdav_path, headers={'Authorization': get_auth_header()})
    print(f"Downloaded watch-later file from {webdav_path} with status code {response.status_code} to {watch_later_path}/{file_hash}")
    if response.status_code == 200:
        local_file = watch_later_path / file_hash
        local_file.write_bytes(response.content)
        return True
    if response.status_code != 404:  # Don't print for normal "not found" cases
        print(f"Failed to download watch-later file. Status code: {response.status_code}")
    return False

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python position_download.py <file_url>")
        sys.exit(1)
    download_from_webdav(sys.argv[1])