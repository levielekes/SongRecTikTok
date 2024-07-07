import os
import requests
import json

# Define the download directory
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'python-version', 'sounds_api')

# Create the directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Path to the JSON file
JSON_FILE = os.path.join(os.getcwd(), 'python-version', 'utils', 'api_urls_received_from_post.json')

def load_urls_from_json():
    with open(JSON_FILE, 'r') as file:
        data = json.load(file)
    return data.get('urls', [])

def download_file(url):
    # Get the filename from the URL
    filename = url.split("/")[-1]
    
    # Full path for the downloaded file
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # Download the file
    try:
        response = requests.get(url, timeout=30)  # Added timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        with open(filepath, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded successfully to {filepath}")
        return True
    except requests.RequestException as e:
        print(f"Failed to download the file from {url}. Error: {str(e)}")
        return False

def clean_json():
    with open(JSON_FILE, 'r') as file:
        data = json.load(file)
    
    data['urls'] = []
    
    with open(JSON_FILE, 'w') as file:
        json.dump(data, file, indent=2)
    
    print("JSON file cleaned. All URLs have been removed.")

if __name__ == "__main__":
    urls = load_urls_from_json()
    successful_downloads = 0
    failed_downloads = 0

    for url in urls:
        if download_file(url):
            successful_downloads += 1
        else:
            failed_downloads += 1
    
    print(f"Download summary: {successful_downloads} successful, {failed_downloads} failed")
    
    clean_json()
    print("JSON file has been cleaned regardless of download outcomes.")