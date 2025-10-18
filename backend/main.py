import os
import json
import subprocess
import threading
import time
import asyncio
from fastapi import FastAPI, Request, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import crawler
import base64
from dotenv import load_dotenv
from position_download import download_from_webdav
from position_upload import get_latest_watch_later_file, upload_to_webdav
from urllib.parse import urlparse
from datetime import datetime, timedelta

app = FastAPI()

# Global event loop reference (set on startup)
app_loop = None

# Path for storing the last sync timestamp
LAST_SYNC_FILE = os.path.join(os.getcwd(), "last_sync.json")
CHECK_INTERVAL = 60 * 60  # Check every hour if sync is needed

@app.on_event("startup")
async def startup_event():
    global app_loop
    app_loop = asyncio.get_running_loop()
    
    # Start the background sync task
    asyncio.create_task(periodic_sync_task())

async def periodic_sync_task():
    """Background task that runs periodically to check if a sync is needed."""
    print("Starting periodic sync background task")
    while True:
        try:
            # Check if a weekly sync is needed
            if is_weekly_sync_needed():
                print("Starting automatic weekly sync...")
                # Create a dummy request for the sync function
                class DummyRequest:
                    def __init__(self):
                        self.base_url = "http://localhost:50005"
                
                dummy_request = DummyRequest()
                await perform_full_sync(dummy_request)
                print("Automatic weekly sync completed")
            
            # Wait for the next check interval
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Error in periodic sync task: {str(e)}")
            await asyncio.sleep(CHECK_INTERVAL)  # Still wait before retrying

def is_weekly_sync_needed():
    """Check if it's been more than a week since the last sync."""
    if not os.path.exists(LAST_SYNC_FILE):
        return True
        
    try:
        with open(LAST_SYNC_FILE, "r") as f:
            sync_data = json.load(f)
            last_sync = datetime.fromisoformat(sync_data.get("last_sync"))
            now = datetime.now()
            # Return True if more than 7 days have passed
            return (now - last_sync) > timedelta(days=7)
    except (json.JSONDecodeError, ValueError, KeyError):
        # If file is invalid or can't be parsed, sync is needed
        return True

# Load environment variables from .env file
load_dotenv()

# Global WebDAV URL; update as needed or set in .env
WEBDAV_URL = os.getenv("WEBDAV_URL")

# Dynamically extract the prefix from WEBDAV_URL.
def get_webdav_prefix(url):
    parsed = urlparse(url)
    return parsed.path.strip("/") + "/"

prefix = get_webdav_prefix(WEBDAV_URL)
print(f"Using WebDAV prefix: {prefix}")

# Add CORS middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to track active uploads by video URL
active_uploads = set()

# Function to save the last sync timestamp
def save_last_sync_time():
    sync_data = {
        "last_sync": datetime.now().isoformat()
    }
    with open(LAST_SYNC_FILE, "w") as f:
        json.dump(sync_data, f)

# Function to check if sync is needed (more than 168 hours since last sync)
def is_sync_needed():
    if not os.path.exists(LAST_SYNC_FILE):
        return True
        
    try:
        with open(LAST_SYNC_FILE, "r") as f:
            sync_data = json.load(f)
            last_sync = datetime.fromisoformat(sync_data.get("last_sync"))
            now = datetime.now()
            # Return True if more than 168 hours have passed
            return (now - last_sync) > timedelta(hours=168)
    except (json.JSONDecodeError, ValueError, KeyError):
        # If file is invalid or can't be parsed, sync is needed
        return True

# Function to get the cached movie data
def get_cached_movies():
    db_path = os.path.join(os.getcwd(), "database.json")
    if os.path.exists(db_path):
        try:
            with open(db_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

# Function to perform a full sync and update the database
async def perform_full_sync(request):
    try:
        # Load the previous database state
        db_path = os.path.join(os.getcwd(), "database.json")
        previous_tree = []
        if os.path.exists(db_path):
            try:
                with open(db_path, "r") as f:
                    previous_tree = json.load(f)
            except json.JSONDecodeError:
                print("Warning: database.json is invalid, starting with empty previous tree")
        
        # Get the current WebDAV tree
        tree = crawler.retrieve_webdav_tree()
        
        # Load database cache
        db_cache = crawler.load_db_cache()
        
        # Clean up orphaned posters from deleted media files
        deleted_count = crawler.cleanup_orphaned_posters(tree, previous_tree, db_cache)
        if deleted_count > 0:
            print(f"Deleted {deleted_count} orphaned poster files")
            
        # Update tree with OMDb info
        for node in tree:
            crawler.update_tree_with_omdb(node, request, db_cache)
        
        # Fix poster fields in db_cache before saving
        crawler.fix_db_cache_posters(db_cache)
        # Save updated database cache
        crawler.save_db_cache(db_cache)
        
        # Fix poster inheritance in the tree before saving
        for node in tree:
            crawler.fix_tree_posters(node)
        # Save the updated tree
        with open(db_path, "w") as f:
            json.dump(tree, f, indent=4)
        
        # Update the last sync time
        save_last_sync_time()
        
        return tree
    except Exception as e:
        print(f"Error during sync: {str(e)}")
        raise e

# Function to periodically upload position files
def upload_position_periodically(video_url):
    print(f"Starting position upload thread for {video_url}")
    try:
        while video_url in active_uploads:
            latest_file, error = get_latest_watch_later_file(max_age_seconds=30)
            if error is None and latest_file is not None:
                if upload_to_webdav(latest_file):
                    print(f"Position file {latest_file.name} uploaded successfully")
                else:
                    print(f"Failed to upload position file {latest_file.name}")
            time.sleep(10)
    except Exception as e:
        print(f"Error in upload thread: {str(e)}")
    finally:
        print(f"Position upload thread for {video_url} stopped")

# Get WebDAV credentials from environment variables
WEBDAV_USERNAME = os.getenv('WEBDAV_USERNAME')
WEBDAV_PASSWORD = os.getenv('WEBDAV_PASSWORD')

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Serve posters using the posters_dir from crawler.py
app.mount("/posters", StaticFiles(directory=crawler.posters_dir), name="posters")

@app.get("/api/movies", response_class=JSONResponse)
async def api_movies(request: Request):
    try:
        if is_sync_needed():
            print("Performing full sync (automatic - over 168 hours)")
            tree = await perform_full_sync(request)
        else:
            print("Using cached movie data (last sync within 168 hours)")
            tree = get_cached_movies()
            
        return tree
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/sync", response_class=JSONResponse)
async def manual_sync(request: Request):
    try:
        print("Performing full sync (manual trigger)")
        tree = await perform_full_sync(request)
        return {"status": "success", "message": "Manual sync completed"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/play", response_class=JSONResponse)
async def play_video(request: Request, data: dict = Body(...)):
    global active_uploads
    try:
        video_path = data.get("path")
        title = data.get("title", "Media Player")
        subs = data.get("subs", [])
        backend_dir = os.path.dirname(__file__)

        # --- Cross-platform MPV Path and Command Configuration ---
        
        # Define the config directory path (relative to main.py)
        config_dir_path = os.path.join(backend_dir, "portable_config")

        # Process video path
        video_path = video_path.lstrip("/")
        if video_path.startswith(prefix):
            video_path = video_path[len(prefix):]
        WEBDAV_URL_BASE = os.getenv("WEBDAV_URL_BASE")
        video_url = WEBDAV_URL_BASE + prefix + video_path

        # Download position file (common)
        print(f"Starting playback for: {video_url}")
        position_found = download_from_webdav(video_url)
        if position_found:
            print(f"Watch position found and loaded for {title}")
        else:
            print(f"No previous watch position found for {title}")

        # Get auth (common)
        if WEBDAV_USERNAME and WEBDAV_PASSWORD:
            credentials = f"{WEBDAV_USERNAME}:{WEBDAV_PASSWORD}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            formatted_auth = f"Authorization: Basic {encoded_credentials}"
            print("Using credentials from .env file")
        else:
            formatted_auth = ""
            print("WARNING: No WebDAV credentials found in .env file")

        # --- OS-specific command building ---
        command_to_run = None
        shell_execute = False

        if os.name == 'nt':  # Windows
            mpv_executable = os.path.join(backend_dir, "mpv.exe")
            if not os.path.exists(mpv_executable):
                return JSONResponse(status_code=500, content={"error": f"MPV executable not found at {mpv_executable}"})
            
            print(f"Using Windows MPV: {mpv_executable}")
            shell_execute = True
            
            # Build the command as a single string for shell=True
            # All paths and arguments with spaces must be quoted
            command_list = [
                'start', '""', '/WAIT',
                f'"{mpv_executable}"',
                f'--config-dir="{config_dir_path}"',
                '--force-window=yes',
                '--fullscreen'
            ]
            if formatted_auth:
                command_list.append(f'--http-header-fields="{formatted_auth}"')
            
            command_list.append(f'--title="{title}"')
            command_list.append(f'--force-media-title="{title}"')
            
            if subs:
                for sub in subs:
                    command_list.append(f'--sub-file="{sub}"')
                print("Subtitle files added:", subs)
            
            command_list.append(f'"{video_url}"')
            
            command_to_run = " ".join(command_list)

        else:  # POSIX (Linux/macOS)
            mpv_executable = "mpv"
            # Check if 'mpv' is in the system path
            if shutil.which(mpv_executable) is None:
                    return JSONResponse(status_code=500, content={"error": "mpv executable not found in system PATH. Please install it."})
            
            print(f"Using system MPV: {mpv_executable}")
            shell_execute = False  # Use shell=False for list-based args
            
            # Build the command as a list of arguments
            # Popen will handle paths with spaces, so no internal quotes are needed
            command_list = [
                mpv_executable,
                f'--config-dir={config_dir_path}',
                '--force-window=yes',
                '--fullscreen'
            ]
            if formatted_auth:
                command_list.append(f'--http-header-fields={formatted_auth}')
            
            command_list.append(f'--title={title}')
            command_list.append(f'--force-media-title={title}')
            
            if subs:
                for sub in subs:
                    command_list.append(f'--sub-file={sub}')
                print("Subtitle files added:", subs)
            
            command_list.append(video_url)
            
            command_to_run = command_list
        
        # --- End of OS-specific logic ---

        print(f"Command string: {command_to_run}")
        
        # Start upload thread (common)
        active_uploads.add(video_url)
        upload_thread = threading.Thread(
            target=upload_position_periodically,
            args=(video_url,),
            daemon=True
        )
        upload_thread.start()
        
        # Launch MPV
        process = subprocess.Popen(command_to_run, shell=shell_execute)
        
        # When MPV closes, stop uploads and notify the frontend.
        def wait_for_mpv():
            process.wait()
            active_uploads.discard(video_url)
            print(f"MPV closed. Stopping uploads for {video_url}")
            if app_loop:
                app_loop.call_soon_threadsafe(asyncio.create_task, manager.broadcast("close_video_popup"))
            else:
                print("App loop not available to send websocket message.")
        
        threading.Thread(target=wait_for_mpv, daemon=True).start()
        
        return {"status": "success", "message": f"Playing {title}", "command": str(command_to_run)}
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/stop_upload", response_class=JSONResponse)
async def stop_upload():
    global active_uploads
    active_uploads.clear()
    return {"status": "success", "message": "Position uploads stopped"}

import shutil

# --- WebSocket Connection Manager ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error sending message: {e}")

manager = ConnectionManager()

from urllib.parse import unquote
import requests
from requests.auth import HTTPBasicAuth

# WebDAV credentials and URL (reuse from crawler.py)
webdav_username = os.getenv('WEBDAV_USERNAME')
webdav_password = os.getenv('WEBDAV_PASSWORD')
webdav_url = os.getenv('WEBDAV_URL')

def webdav_delete(path):
    """Delete a file or folder on the WebDAV server."""
    if not all([webdav_username, webdav_password, webdav_url]):
        raise Exception("WebDAV credentials not set in .env")
    # Ensure path is not double-encoded
    path_decoded = unquote(path)
    # Compose full URL
    if path_decoded.startswith("/"):
        path_decoded = path_decoded[1:]
    full_url = webdav_url.rstrip("/") + "/" + path_decoded
    response = requests.request(
        "DELETE",
        full_url,
        auth=HTTPBasicAuth(webdav_username, webdav_password),
        timeout=60
    )
    return response

@app.post("/api/delete", response_class=JSONResponse)
async def api_delete(request: Request, data: dict = Body(...)):
    """
    Delete a file or folder and update all relevant databases.
    Expects JSON: { "path": "...", "type": "FOLDER" | "VIDEO" }
    """
    try:
        rel_path = data.get("path")
        item_type = data.get("type")
        if not rel_path or not item_type:
            return JSONResponse(status_code=400, content={"error": "Missing path or type."})

        # Remove leading slash if present
        rel_path = rel_path.lstrip("/")
        # Remove prefix if present
        if rel_path.startswith(prefix):
            rel_path = rel_path[len(prefix):]
        # URL-decode the path for WebDAV
        rel_path_decoded = unquote(rel_path)

        # Prevent deletion of the root directory
        if rel_path_decoded.strip() == "":
            return JSONResponse(status_code=400, content={"error": "Refusing to delete the root directory."})

        # Delete file or folder on WebDAV
        webdav_response = webdav_delete(rel_path_decoded)
        if not (200 <= webdav_response.status_code < 300):
            return JSONResponse(
                status_code=404,
                content={"error": f"WebDAV delete failed: {webdav_response.status_code} {webdav_response.reason} {webdav_response.text}"}
            )

        # If deleting a movie file, check if parent folder should also be deleted
        # Only applies if type is VIDEO
        if item_type == "VIDEO":
            import posixpath
            from xml.etree import ElementTree
            # Get parent folder path (relative to media root)
            parent_folder = posixpath.dirname(rel_path_decoded)
            if parent_folder and parent_folder != ".":
                # List all items in the parent folder via WebDAV PROPFIND (Depth: 1)
                webdav_propfind_url = webdav_url.rstrip("/") + "/" + parent_folder
                headers = {"Depth": "1"}
                propfind_body = """<?xml version="1.0" encoding="utf-8" ?>
                    <d:propfind xmlns:d="DAV:">
                        <d:allprop/>
                    </d:propfind>"""
                propfind_response = requests.request(
                    "PROPFIND",
                    webdav_propfind_url,
                    data=propfind_body,
                    headers=headers,
                    auth=HTTPBasicAuth(webdav_username, webdav_password),
                    timeout=60
                )
                if propfind_response.status_code in (207, 207):
                    # Parse XML to get all files/folders in the parent folder (not recursive)
                    tree = ElementTree.fromstring(propfind_response.content)
                    files = []
                    for response in tree.findall("{DAV:}response"):
                        href = response.find("{DAV:}href")
                        if href is not None:
                            path = href.text
                            # Remove leading webdav path and parent_folder
                            if path.startswith("/"):
                                path = path[1:]
                            if path.startswith(prefix):
                                path = path[len(prefix):]
                            # Only consider files inside the parent folder (not the parent itself)
                            if path and path != parent_folder and not path.endswith("/"):
                                files.append(path)
                    # Remove the file that was just deleted from the list
                    deleted_file_name = posixpath.basename(rel_path_decoded)
                    files = [f for f in files if posixpath.basename(f) != deleted_file_name]
                    # Check for any other movie files
                    movie_exts = (".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm")
                    other_movies = [f for f in files if f.lower().endswith(movie_exts)]
                    # Check for subfolders (if any)
                    subfolders = [f for f in files if "/" in f]
                    # If no other movie files and no subfolders, delete all files and the folder
                    if not other_movies and not subfolders:
                        for f in files:
                            webdav_delete(posixpath.join(parent_folder, f))
                        # Delete the folder itself
                        webdav_delete(parent_folder)

        # Remove from database.json
        db_path = os.path.join(os.getcwd(), "database.json")
        if os.path.exists(db_path):
            try:
                with open(db_path, "r") as f:
                    db = json.load(f)
                def remove_entry(items):
                    new_items = []
                    for item in items:
                        if item.get("path") == data["path"]:
                            continue
                        if item.get("type") == "FOLDER" and "children" in item:
                            item["children"] = remove_entry(item["children"])
                        new_items.append(item)
                    return new_items
                db = remove_entry(db)
                with open(db_path, "w") as f:
                    json.dump(db, f, indent=4)
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": f"Failed to update database.json: {e}"})

        # Remove from db_cache.json
        db_cache_path = os.path.join(os.getcwd(), "db_cache.json")
        if os.path.exists(db_cache_path):
            try:
                with open(db_cache_path, "r") as f:
                    db_cache = json.load(f)
                db_cache.pop(data["path"], None)
                with open(db_cache_path, "w") as f:
                    json.dump(db_cache, f, indent=4)
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": f"Failed to update db_cache.json: {e}"})

        # Remove from last_sync.json if present
        last_sync_path = os.path.join(os.getcwd(), "last_sync.json")
        if os.path.exists(last_sync_path):
            try:
                with open(last_sync_path, "r") as f:
                    last_sync = json.load(f)
                if isinstance(last_sync, dict) and data["path"] in last_sync:
                    del last_sync[data["path"]]
                    with open(last_sync_path, "w") as f:
                        json.dump(last_sync, f, indent=4)
            except Exception:
                pass  # Ignore errors here

        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

        # Remove from database.json
        db_path = os.path.join(os.getcwd(), "database.json")
        if os.path.exists(db_path):
            try:
                with open(db_path, "r") as f:
                    db = json.load(f)
                def remove_entry(items):
                    new_items = []
                    for item in items:
                        if item.get("path") == data["path"]:
                            continue
                        if item.get("type") == "FOLDER" and "children" in item:
                            item["children"] = remove_entry(item["children"])
                        new_items.append(item)
                    return new_items
                db = remove_entry(db)
                with open(db_path, "w") as f:
                    json.dump(db, f, indent=4)
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": f"Failed to update database.json: {e}"})

        # Remove from db_cache.json
        db_cache_path = os.path.join(os.getcwd(), "db_cache.json")
        if os.path.exists(db_cache_path):
            try:
                with open(db_cache_path, "r") as f:
                    db_cache = json.load(f)
                db_cache.pop(data["path"], None)
                with open(db_cache_path, "w") as f:
                    json.dump(db_cache, f, indent=4)
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": f"Failed to update db_cache.json: {e}"})

        # Remove from last_sync.json if present
        last_sync_path = os.path.join(os.getcwd(), "last_sync.json")
        if os.path.exists(last_sync_path):
            try:
                with open(last_sync_path, "r") as f:
                    last_sync = json.load(f)
                if isinstance(last_sync, dict) and data["path"] in last_sync:
                    del last_sync[data["path"]]
                    with open(last_sync_path, "w") as f:
                        json.dump(last_sync, f, indent=4)
            except Exception:
                pass  # Ignore errors here

        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Optionally process incoming messages
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=50005)
