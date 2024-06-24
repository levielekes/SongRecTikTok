import os
import psycopg2
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

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

        # Define the date two weeks ago from now
        two_weeks_ago = datetime.now() - timedelta(weeks=2)

        # Query to fetch tiktok_play_url and tiktok_sound_id column values with the specified conditions
        query = '''
        SELECT tiktok_play_url, tiktok_sound_id 
        FROM public.sounds_data_tiktoksounds 
        LEFT JOIN public.sounds_data_shazamsounds 
        ON public.sounds_data_tiktoksounds.tiktok_sound_id = public.sounds_data_shazamsounds.shazam_sound_id 
        WHERE shazam_sound_id IS NULL 
        OR (tiktok_sound_last_checked_by_shazam_with_no_result IS NOT NULL 
            AND tiktok_sound_last_checked_by_shazam_with_no_result < %s)
        '''
        cursor.execute(query, (two_weeks_ago,))

        # Fetch all rows
        rows = cursor.fetchall()

        # Download each file and save it to the directory
        for row in rows:
            tiktok_play_url, tiktok_sound_id = row
            result = {"url": tiktok_play_url, "status": "success"}
            try:
                # Determine the file name based on the URL and tiktok_sound_id
                if tiktok_play_url.endswith('.mp3'):
                    file_name = f"{tiktok_sound_id}.mp3"
                else:
                    file_extension = os.path.splitext(tiktok_play_url)[1]
                    file_name = f"{tiktok_sound_id}{file_extension}"
                
                file_path = os.path.join(DOWNLOAD_DIR, file_name)

                # Download the file
                response = requests.get(tiktok_play_url)
                response.raise_for_status()

                # Save the file to the specified directory
                with open(file_path, 'wb') as file:
                    file.write(response.content)

                result["file_path"] = file_path

                # Print the tiktok_play_url to the terminal
                print(f"Downloaded: {tiktok_play_url}")
            except Exception as download_error:
                result["status"] = "error"
                result["error_message"] = str(download_error)
                print(f"Error downloading {tiktok_play_url}: {download_error}")
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
