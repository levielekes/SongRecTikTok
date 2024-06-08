import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

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

        # Print play_url values
        for row in rows:
            print(row[0])

    except Exception as error:
        print(f"Error fetching data: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    fetch_play_urls()
