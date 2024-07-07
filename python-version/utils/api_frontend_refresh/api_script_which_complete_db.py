import os
import requests

# Define the download directory
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'python-version', 'sounds_api')

# Create the directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Define the URL of the file to download
url = "https://sf16-ies-music.tiktokcdn.com/obj/ies-music-euttp/7351481446513445664.mp3"

def download_file(url):
    # Get the filename from the URL
    filename = url.split("/")[-1]
    
    # Full path for the downloaded file
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # Download the file
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(filepath, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded successfully to {filepath}")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")

if __name__ == "__main__":
    download_file(url)