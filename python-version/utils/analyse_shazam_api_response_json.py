import json
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

def update_songs_and_sounds(data):
    try:
        # Connect to your postgres DB
        conn = psycopg2.connect(DATABASE_URL)
        # Create a cursor object
        cursor = conn.cursor()

        for item in data:
            file_path = item.get("file", "")
            tiktok_sound_id = os.path.splitext(os.path.basename(file_path))[0]

            result = item.get("result", {})
            track_info = result.get("track", {})
            share_info = track_info.get("share", {})
            images_info = track_info.get("images", {})

            # Extract the values as specified
            shazam_photo_url = images_info.get("background", None)
            shazam_song_name = share_info.get("subject", None)
            shazam_track_url = share_info.get("href", None)

            # Check if any of the required fields are missing
            missing_data = not all([shazam_photo_url, shazam_song_name, shazam_track_url])

            # Create a dictionary for the columns to update
            update_data = {
                "shazam_image_url": shazam_photo_url if shazam_photo_url not in [None, "N/A"] else None,
                "shazam_song_name": shazam_song_name if shazam_song_name not in [None, "N/A"] else None,
                "shazam_url": shazam_track_url if shazam_track_url not in [None, "N/A"] else None,
            }

            # Filter out keys with None values
            update_data = {key: value for key, value in update_data.items() if value is not None}

            # Add the tiktok_sound_last_checked_by_shazam_with_no_result field if necessary
            if missing_data:
                update_data["tiktok_sound_last_checked_by_shazam_with_no_result"] = datetime.now()

            if update_data:
                set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
                query = f"UPDATE public.sounds_data_tiktoksounds SET {set_clause} WHERE tiktok_sound_id = %s"
                cursor.execute(query, list(update_data.values()) + [tiktok_sound_id])

        # Commit the changes
        conn.commit()

        # Print updated records
        for item in data:
            file_path = item.get("file", "")
            tiktok_sound_id = os.path.splitext(os.path.basename(file_path))[0]

            select_query = sql.SQL("""
                SELECT tiktok_sound_id, shazam_image_url, shazam_song_name, shazam_url
                FROM public.sounds_data_tiktoksounds
                WHERE tiktok_sound_id = %s
            """)
            cursor.execute(select_query, (tiktok_sound_id,))
            record = cursor.fetchone()
            if record:
                print(f"Updated record for tiktok_sound_id: {tiktok_sound_id}")
                print(f"  shazam_image_url: {record[1]}")
                print(f"  shazam_song_name: {record[2]}")
                print(f"  shazam_url: {record[3]}")
                print("\n")

        # Close the cursor and connection
        cursor.close()
        conn.close()
        print("Database updated successfully.")

    except Exception as e:
        print(f"Error: {e}")

def clean_sounds_directory(directory_path):
    try:
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        print(f"Cleaned all files in directory: {directory_path}")
    except Exception as e:
        print(f"Error while cleaning directory: {e}")

def analyse_shazam_api_response_json():
    # Load the JSON data from the file with UTF-8 encoding
    shazam_api_response_path = os.getenv('SHAZAM_API_RESPONSE_PATH')
    with open(shazam_api_response_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    update_songs_and_sounds(data)

    # Clean the sounds directory
    clean_sounds_directory(os.getenv('SOUNDS_DIR'))

if __name__ == "__main__":
    analyse_shazam_api_response_json()
