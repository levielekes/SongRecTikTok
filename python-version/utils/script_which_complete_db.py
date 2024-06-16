import os
import psycopg2
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

# Define the directory to save the downloaded files
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'python-version/sounds')

# Create the directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def fetch_tiktok_play_urls():
    download_results = []
    try:
        # Connect to the PostgreSQL database using the DATABASE_URL
        connection = psycopg2.connect(DATABASE_URL)
        
        cursor = connection.cursor()

        # Query to fetch tiktok_play_url column values where shazam_url is null, limited to 5 entries
        query = 'SELECT tiktok_play_url FROM public.sounds_data_songsandsounds WHERE shazam_url IS NULL LIMIT 10'
        cursor.execute(query)

        # Fetch all rows
        rows = cursor.fetchall()

        # Extract tiktok_play_url values
        tiktok_play_urls = [row[0] for row in rows]

        # Download each file and save it to the directory
        for url in tiktok_play_urls:
            result = {"url": url, "status": "success"}
            try:
                # Get the file name from the URL
                file_name = os.path.basename(url)
                file_path = os.path.join(DOWNLOAD_DIR, file_name)

                # Download the file
                response = requests.get(url)
                response.raise_for_status()

                # Save the file to the specified directory
                with open(file_path, 'wb') as file:
                    file.write(response.content)

                result["file_path"] = file_path
            except Exception as download_error:
                result["status"] = "error"
                result["error_message"] = str(download_error)
            finally:
                download_results.append(result)

    except Exception as error:
        print(f"Error fetching data: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

    # Save results to a JSON file
    json_file_path = os.path.join(os.getcwd(), 'download_results.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(download_results, json_file, indent=4)

if __name__ == "__main__":
    fetch_tiktok_play_urls()