import os
import psycopg2
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

# Define the directory to save the downloaded files
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'python-version/sounds')

# Create the directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def fetch_play_urls():
    try:
        # Connect to the PostgreSQL database using the DATABASE_URL
        connection = psycopg2.connect(DATABASE_URL)
        
        cursor = connection.cursor()

        # Query to fetch play_url column values where shazam_url is null, limited to 5 entries
        query = 'SELECT play_url FROM public.sounds_data_songsandsounds WHERE shazam_url IS NULL LIMIT 5'
        cursor.execute(query)

        # Fetch all rows
        rows = cursor.fetchall()

        # Extract play_url values
        play_urls = [row[0] for row in rows]

        # Download each file and save it to the directory
        for url in play_urls:
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

                print(f"Downloaded and saved: {file_path}")

            except Exception as download_error:
                print(f"Error downloading {url}: {download_error}")

    except Exception as error:
        print(f"Error fetching data: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    fetch_play_urls()
