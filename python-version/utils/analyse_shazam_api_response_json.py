import json
import os
import re

from datetime import datetime
from typing import Optional, Dict, Any

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')


def extract_shazam_sound_id(url):
    match = re.search(r'(?:track|song)/(\d+)', url)
    return match.group(1) if match else None


def get_shazam_label_name(track_info: Dict[str, Any]) -> Optional[str]:
    sections = track_info.get("sections", [])

    if not sections:
        return None

    song_section = next((section for section in sections if section.get("type") == "SONG"), None)

    if not song_section:
        return None

    metadata = song_section.get("metadata", [])

    if not metadata:
        return None

    # Find the metadata with title "Label"
    label = next((meta for meta in metadata if meta.get("title") == "Label"), {})

    # Get the text value from the label
    label_value = label.get("text", None)

    return label_value


def update_shazam_info(data):
    try:
        # Connect to postgres DB
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
            shazam_image_url = images_info.get("background", None)
            shazam_name_of_sound = share_info.get("subject", None)
            shazam_track_url = share_info.get("href", None)

            shazam_label_name = get_shazam_label_name(track_info)

            # Extract Shazam sound ID from the URL
            shazam_sound_id = extract_shazam_sound_id(shazam_track_url) if shazam_track_url else None

            # Debug print statements
            print(f"file_path: {file_path}")
            print(f"tiktok_sound_id: {tiktok_sound_id}")
            print(f"shazam_image_url: {shazam_image_url}")
            print(f"shazam_name_of_sound: {shazam_name_of_sound}")
            print(f"shazam_track_url: {shazam_track_url}")
            print(f"shazam_sound_id: {shazam_sound_id}")
            print(f"shazam_label_name: {shazam_label_name}")

            # Check if any of the required fields are missing
            if not all([shazam_image_url, shazam_name_of_sound, shazam_sound_id]):
                print("Missing required Shazam data, skipping insert.")

                # Update tiktok_sound_last_checked_by_shazam_with_no_result if shazamsounds_id is None
                update_query_no_result = """
                    UPDATE public.sounds_data_tiktoksounds
                    SET tiktok_sound_last_checked_by_shazam_with_no_result = %s
                    WHERE tiktok_sound_id = %s AND shazamsounds_id IS NULL;
                """
                cursor.execute(update_query_no_result, (datetime.now(), tiktok_sound_id))
                continue

            try:
                shazamsounds_id = create_or_update_shazam_sound(
                    cursor, shazam_sound_id, shazam_image_url, shazam_name_of_sound, shazam_label_name)

                update_query = """
                    UPDATE public.sounds_data_tiktoksounds
                    SET shazamsounds_id = %s
                    WHERE tiktok_sound_id = %s;
                """
                cursor.execute(update_query, (shazamsounds_id, tiktok_sound_id))
                print(f"Updated TikTok sound ID {tiktok_sound_id} with Shazam sound ID {shazamsounds_id}.")

            except Exception as e:
                print(f"Error: {e}")
                continue

        # Commit the changes
        conn.commit()

        # Print updated records
        for item in data:
            file_path = item.get("file", "")
            tiktok_sound_id = os.path.splitext(os.path.basename(file_path))[0]

            select_query = sql.SQL("""
                SELECT tiktok_sound_id, shazamsounds_id
                FROM public.sounds_data_tiktoksounds
                WHERE tiktok_sound_id = %s
            """)
            cursor.execute(select_query, (tiktok_sound_id,))
            record = cursor.fetchone()
            if record:
                print(f"Updated record for tiktok_sound_id: {tiktok_sound_id}")
                print(f"  shazamsounds_id: {record[1]}")
                print("\n")

        # Close the cursor and connection
        cursor.close()
        conn.close()
        print("Database updated successfully.")

    except Exception as e:
        print(f"Error: {e}")


def create_or_update_shazam_sound(cursor, shazam_sound_id, shazam_image_url, shazam_name_of_sound, shazam_label_name):
    check_query = "SELECT id, shazam_label_name FROM public.sounds_data_shazamsounds WHERE shazam_sound_id = %s;"
    cursor.execute(check_query, (shazam_sound_id,))
    existing_record = cursor.fetchone()

    if existing_record:
        shazamsounds_id, existing_shazam_label_name = existing_record

        if (shazam_label_name and shazam_label_name != existing_shazam_label_name):
            update_query = """
                UPDATE public.sounds_data_shazamsounds
                SET shazam_label_name = %s
                WHERE id = %s;
            """
            cursor.execute(update_query, (shazam_label_name, shazamsounds_id))
    else:
        # Insert into public.sounds_data_shazamsounds
        insert_query = """
            INSERT INTO public.sounds_data_shazamsounds (shazam_image_url, shazam_name_of_sound, shazam_sound_id, shazam_label_name)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """
        cursor.execute(insert_query, (shazam_image_url, shazam_name_of_sound, shazam_sound_id, shazam_label_name))
        shazamsounds_id = cursor.fetchone()[0]

        print(f"Inserted new Shazam sound ID {shazam_sound_id} with ID {shazamsounds_id}.")

    return shazamsounds_id


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

    update_shazam_info(data)

    # Clean the sounds directory
    clean_sounds_directory(os.getenv('SOUNDS_DIR'))


if __name__ == "__main__":
    analyse_shazam_api_response_json()
