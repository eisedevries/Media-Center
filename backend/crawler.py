import os
import json
import datetime
import xml.etree.ElementTree as ET
from collections import OrderedDict
from math import floor
import hashlib
import requests
from requests.auth import HTTPBasicAuth
from guessit import guessit
from dotenv import load_dotenv

# Load environment variables.
load_dotenv()

# OMDb and posters configuration.
omdb_api_key = os.getenv('omdb_api_key')
posters_dir = os.path.join(os.path.dirname(__file__), "posters")
if not os.path.exists(posters_dir):
    os.makedirs(posters_dir)
    

# Create the posters directory if it doesn't exist.
if not os.path.exists(posters_dir):
    os.makedirs(posters_dir)

# WebDAV credentials.
webdav_username = os.getenv('WEBDAV_USERNAME')
webdav_password = os.getenv('WEBDAV_PASSWORD')
webdav_url = os.getenv('WEBDAV_URL')

if not all([webdav_username, webdav_password, webdav_url]):
    raise Exception("WebDAV credentials not set in .env")

# Define file type extension lists.
VIDEO_EXTENSIONS = ['3g2', '3gp', 'avi', 'flv', 'm2ts', 'm4v', 'mj2', 'mkv', 'mov', 'mp4',
                    'mpeg', 'mpg', 'ogv', 'rmvb', 'ts', 'webm', 'wmv', 'y4m']
SUBTITLE_EXTENSIONS = ['ass', 'idx', 'lrc', 'mks', 'pgs', 'rt', 'sbv', 'scc', 'smi', 'srt',
                       'ssa', 'sub', 'sup', 'utf', 'utf-8', 'utf8', 'vtt']

def determine_file_type(name):
    ext = name.split('.')[-1].lower()
    if ext in VIDEO_EXTENSIONS:
        return "VIDEO"
    elif ext in SUBTITLE_EXTENSIONS:
        return "SUBTITLE"
    else:
        return "FILE"

# --- WebDAV Retrieval & Tree Building ---

headers = {
    'Depth': 'infinity',
    'Content-Type': 'text/xml'
}
body = '''<?xml version="1.0" encoding="utf-8" ?>
<propfind xmlns="DAV:">
  <prop>
    <displayname/>
    <getlastmodified/>
    <getcontentlength/>
    <resourcetype/>
  </prop>
</propfind>'''

def retrieve_webdav_tree():
    """Retrieve all WebDAV data and build a nested tree structure with guessit info."""
    response = requests.request(
        'PROPFIND',
        webdav_url,
        headers=headers,
        data=body,
        auth=HTTPBasicAuth(webdav_username, webdav_password),
        timeout=60
    )
    if response.status_code != 207:
        raise Exception(f"Error retrieving WebDAV data: status {response.status_code}")
    root_elem = ET.fromstring(response.content)
    ns = {'d': 'DAV:'}

    def parse_response(elem):
        items = []
        for resp in elem.findall('d:response', ns):
            href_elem = resp.find('d:href', ns)
            if href_elem is None:
                continue
            href = href_elem.text

            prop = resp.find('d:propstat/d:prop', ns)
            displayname_elem = prop.find('d:displayname', ns) if prop is not None else None
            displayname = displayname_elem.text if displayname_elem is not None else ''

            last_modified_elem = prop.find('d:getlastmodified', ns) if prop is not None else None
            last_modified = last_modified_elem.text if last_modified_elem is not None else ''

            content_length_elem = prop.find('d:getcontentlength', ns) if prop is not None else None
            try:
                size = int(content_length_elem.text) if (content_length_elem is not None and content_length_elem.text) else 0
            except ValueError:
                size = 0

            resourcetype = prop.find('d:resourcetype', ns) if prop is not None else None
            is_collection = (resourcetype is not None and resourcetype.find('d:collection', ns) is not None)

            if is_collection:
                item_type = "FOLDER"
            else:
                candidate = displayname if displayname else os.path.basename(href.rstrip('/'))
                item_type = determine_file_type(candidate)
            name = displayname if displayname else os.path.basename(href.rstrip('/'))

            items.append({
                "href": href,
                "name": name,
                "last_modified": last_modified,
                "type": item_type,
                "size": size
            })
        return items

    flat_items = parse_response(root_elem)
    # Build nested tree from flat items using href paths.
    nodes = {}
    for item in flat_items:
        path = item["href"]
        node = {
            "name": item["name"],
            "path": path,
            "type": item["type"],
            "last_modified": item["last_modified"],
            "size": item["size"]
        }
        if item["type"] == "FOLDER":
            node["children"] = []
        nodes[path] = node

    tree_list = []
    for path, node in nodes.items():
        parent_path = os.path.dirname(path.rstrip('/')) + '/'
        if parent_path == path or parent_path not in nodes:
            tree_list.append(node)
        else:
            nodes[parent_path].setdefault("children", []).append(node)
    # Compute folder sizes recursively.
    def compute_folder_size(node):
        if node["type"] != "FOLDER":
            return node.get("size", 0)
        total = 0
        for child in node.get("children", []):
            total += compute_folder_size(child)
        node["size"] = total
        return total
    for node in tree_list:
        compute_folder_size(node)
    # Process each node with guessit and reassemble keys.
    def process_node(node):
        try:
            g = guessit(node["name"])
        except Exception as e:
            print(f"Guessit error for {node['name']}: {e}")
            g = {}
        new_node = OrderedDict()
        new_node["name"] = node["name"]
        new_node["title"] = g.get("title") if "title" in g and g["title"] else None
        new_node["year"] = g.get("year") if "year" in g and g["year"] else None
        new_node["source"] = g.get("source") if "source" in g and g["source"] else None
        # Always include "season" key for every node (file or folder)
        new_node["season"] = g.get("season") if "season" in g and g["season"] else None
        # For file nodes, add additional keys if available.
        if node["type"] != "FOLDER":
            new_node["episode"] = g.get("episode") if "episode" in g and g["episode"] else None
            new_node["episode_title"] = g.get("episode_title") if "episode_title" in g and g["episode_title"] else None
        new_node["path"] = node["path"]
        new_node["last_modified"] = node["last_modified"]
        if node["type"] == "FOLDER":
            new_node["type"] = "FOLDER"
        else:
            guessit_type = g.get("type", "").lower()
            new_node["type"] = guessit_type  # Will later be updated by OMDb.
            new_node["file-type"] = node["type"]
        new_node["size"] = node["size"]
        if node["type"] == "FOLDER":
            children = []
            for child in node.get("children", []):
                children.append(process_node(child))
            new_node["children"] = children
        return new_node

    final_tree = [process_node(node) for node in tree_list]
    # If there is only one top-level folder, skip it by returning its children
    if len(final_tree) == 1 and final_tree[0]["type"] == "FOLDER":
        final_tree = final_tree[0].get("children", [])
    return final_tree

def cleanup_orphaned_posters(current_tree, previous_tree, db_cache):
    """
    Compare current and previous media trees to find deleted items and remove their poster files.
    
    Args:
        current_tree: The newly retrieved WebDAV tree
        previous_tree: The previous tree from database.json
        db_cache: The OMDb API cache dictionary
    
    Returns:
        int: Number of poster files deleted
    """
    # Extract all file paths from current tree
    current_paths = set()
    
    def collect_paths(node):
        if node.get("type") != "FOLDER":
            current_paths.add(node.get("path"))
        for child in node.get("children", []):
            collect_paths(child)
    
    for node in current_tree:
        collect_paths(node)
    
    # Collect items from previous tree that had posters
    previous_items = []
    
    def collect_items_with_posters(node):
        if node.get("type") != "FOLDER" and node.get("poster_filename"):
            previous_items.append({
                "path": node.get("path"),
                "poster_filename": node.get("poster_filename"),
                "file_name": node.get("name")
            })
        for child in node.get("children", []):
            collect_items_with_posters(child)
    
    for node in previous_tree:
        collect_items_with_posters(node)
    
    # Find and delete orphaned posters
    deleted_count = 0
    for item in previous_items:
        if item["path"] not in current_paths:
            # This item was deleted and had a poster file
            poster_path = os.path.join(posters_dir, item["poster_filename"])
            if os.path.exists(poster_path):
                try:
                    os.remove(poster_path)
                    print(f"Deleted orphaned poster: {item['poster_filename']}")
                    deleted_count += 1
                    
                    # Also clean up the db_cache entry
                    if item["file_name"] in db_cache:
                        del db_cache[item["file_name"]]
                        
                except OSError as e:
                    print(f"Error deleting poster {item['poster_filename']}: {e}")
    
    return deleted_count

# --- OMDb Integration Functions (for files only) ---

def get_poster_filename(title):
    # Generate an MD5 hash of the title and take the first 20 characters
    hash_digest = hashlib.md5(title.encode("utf-8")).hexdigest()[:20]
    return f"{hash_digest}.jpg"


def load_db_cache():
    db_path = os.path.join(os.getcwd(), "db_cache.json")
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            return json.load(f)
    else:
        return {}

def save_db_cache(db):
    db_path = os.path.join(os.getcwd(), "db_cache.json")
    with open(db_path, "w") as f:
        json.dump(db, f, indent=4)

def convert_runtime(runtime_str):
    if runtime_str and runtime_str.endswith(" min"):
        try:
            minutes = int(runtime_str.split()[0])
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h{mins}m"
        except ValueError:
            return None
    return runtime_str

def convert_votes(votes_int):
    if votes_int >= 1_000_000:
        millions = floor(votes_int / 100000) / 10
        return f"{millions}M"
    elif votes_int >= 1000:
        if votes_int < 10_000:
            thousands = floor(votes_int / 100) / 10
            return f"{thousands}K"
        else:
            thousands = votes_int // 1000
            return f"{thousands}K"
    else:
        return str(votes_int)

def get_movie_details(request, title, year, file_name, last_modified, db_cache):
    # If the item is in the cache and its last_modified hasn't changed, return the cached record.
    if file_name in db_cache:
        cached = db_cache[file_name]
        if cached.get("last_modified") == last_modified:
            return cached

    # Otherwise, build a new record.
    record = {
        "file_name": file_name,
        "title": title,
        "year": year,
        "poster": None,
        "api_found": False,
        "poster_filename": None,
        "imdb": None,
        "duration": None,
        "director": None,
        "genre": None,
        "plot": None,
        "language": None,
        "actors": None,
        "imdbID": None,
        "imdbVotes": None,
        "boxOffice": None,
        "type": None,
        "omdb_title": None,
        "last_modified": last_modified  # Save the current last_modified timestamp.
    }
    params = {"apikey": omdb_api_key, "t": title, "plot": "full"}
    if year:
        params["y"] = year
    try:
        response = requests.get("http://www.omdbapi.com/", params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                record["api_found"] = True
                # Retrieve OMDb Title and update record.
                omdb_title = data.get("Title")
                if omdb_title and omdb_title != "N/A":
                    record["omdb_title"] = omdb_title
                else:
                    record["omdb_title"] = None

                record["imdb"] = data.get("imdbRating")
                runtime = data.get("Runtime")
                record["duration"] = convert_runtime(runtime)
                record["director"] = data.get("Director")
                record["genre"] = data.get("Genre")
                record["plot"] = data.get("Plot")
                language = data.get("Language")
                if language:
                    record["language"] = language.split(",")[0].strip()
                record["actors"] = data.get("Actors")
                record["imdbID"] = data.get("imdbID")
                votes_str = data.get("imdbVotes")
                if votes_str and votes_str != "N/A":
                    try:
                        votes_int = int(votes_str.replace(",", ""))
                        record["imdbVotes"] = convert_votes(votes_int)
                    except ValueError:
                        record["imdbVotes"] = votes_str
                record["boxOffice"] = data.get("BoxOffice")
                record["type"] = data.get("Type")
                poster_url = data.get("Poster")
                if poster_url and poster_url != "N/A":
                    poster_filename = get_poster_filename(title)
                    poster_filepath = os.path.join(posters_dir, poster_filename)
                    img_response = requests.get(poster_url, stream=True)
                    if img_response.status_code == 200:
                        with open(poster_filepath, "wb") as f:
                            for chunk in img_response.iter_content(1024):
                                f.write(chunk)
                        record["poster_filename"] = poster_filename
                        record["poster"] = str(request.url_for("posters", path=poster_filename))
                    else:
                        # Poster download failed, but if poster_filename is set, still set poster URL
                        if poster_filename:
                            record["poster_filename"] = poster_filename
                            record["poster"] = str(request.url_for("posters", path=poster_filename))
    except Exception as e:
        print(f"Error querying OMDb API for {title}: {e}")
    db_cache[file_name] = record
    return record

# --- New Tree Cache Functions for last_modified timestamps ---

def load_tree_cache():
    tree_cache_path = os.path.join(os.getcwd(), "tree_cache.json")
    if os.path.exists(tree_cache_path):
        with open(tree_cache_path, "r") as f:
            return json.load(f)
    else:
        return {}

def save_tree_cache(tree_cache):
    tree_cache_path = os.path.join(os.getcwd(), "tree_cache.json")
    with open(tree_cache_path, "w") as f:
        json.dump(tree_cache, f, indent=4)

# --- Updated update_tree_with_omdb Function with Tree Caching ---
def update_tree_with_omdb(node, request, db_cache, tree_cache=None):
    """
    Recursively update file nodes (non-folders) with OMDb info.
    For each node (folder or file), if its last_modified timestamp matches what is already saved
    in the tree cache (from a previous run), then skip updating and reuse the cached node.
    """
    if tree_cache is None:
        tree_cache = {}
        
    # Check if this node has been previously cached and unchanged.
    cached_node = tree_cache.get(node["path"])
    if cached_node and cached_node.get("last_modified") == node.get("last_modified"):
        return cached_node

    if node["type"] != "FOLDER":
        title = node.get("title")
        year = node.get("year")
        if title:
            details = get_movie_details(request, title, year, node["name"], node["last_modified"], db_cache)
            node["poster"] = details.get("poster")
            node["api_found"] = details.get("api_found")
            node["poster_filename"] = details.get("poster_filename")
            node["imdb"] = details.get("imdb")
            if node.get("season") is not None and node.get("episode") is not None:
                node.pop("duration", None)
            else:
                node["duration"] = details.get("duration")
            node["director"] = details.get("director")
            node["genre"] = details.get("genre")
            node["plot"] = details.get("plot")
            node["language"] = details.get("language")
            node["actors"] = details.get("actors")
            node["imdbID"] = details.get("imdbID")
            node["imdbVotes"] = details.get("imdbVotes")
            node["boxOffice"] = details.get("boxOffice")
            # Override with OMDb type.
            node["type"] = details.get("type")
            
            # Only update title if this item was not already in the cache (i.e. updated now)
            # Compare OMDb title with guessit title and update if necessary.
            omdb_title = details.get("omdb_title")
            guessit_title = node.get("title")
            if omdb_title and omdb_title != guessit_title:
                node["title"] = omdb_title
            
            # If the type is "movie", remove "season" and "episode" keys.
            if node.get("type") == "movie":
                node.pop("season", None)
                node.pop("episode", None)
    else:
        updated_children = []
        for child in node.get("children", []):
            updated_child = update_tree_with_omdb(child, request, db_cache, tree_cache)
            updated_children.append(updated_child)
        node["children"] = updated_children

    # Save the updated node in the tree cache.
    tree_cache[node["path"]] = node
    return node

# --- Poster Fix Utilities ---

def fix_db_cache_posters(db):
    """
    For each entry in the db_cache dict, if 'poster' is null/missing and 'poster_filename' is set,
    set 'poster' to the correct URL.
    """
    for entry in db.values():
        if (not entry.get("poster")) and entry.get("poster_filename"):
            entry["poster"] = f"http://127.0.0.1:50005/posters/{entry['poster_filename']}"

def fix_tree_posters(node, inherited_poster=None):
    """
    Recursively fix poster inheritance in a tree node.
    - If 'poster' is null/missing and 'poster_filename' is set, set 'poster' to the correct URL.
    - If 'poster' is still null/missing and inherited_poster is set, inherit it.
    - Recurse into children.
    """
    # Set poster from poster_filename if possible
    if (not node.get("poster")) and node.get("poster_filename"):
        node["poster"] = f"http://127.0.0.1:50005/posters/{node['poster_filename']}"
    # Inherit poster if still missing
    if not node.get("poster") and inherited_poster:
        node["poster"] = inherited_poster
    # Pass down the nearest non-null poster
    next_inherited = node.get("poster") or inherited_poster
    for child in node.get("children", []):
        fix_tree_posters(child, next_inherited)
