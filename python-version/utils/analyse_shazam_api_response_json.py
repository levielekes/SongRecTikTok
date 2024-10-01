import json
import os
import re

from datetime import datetime
from typing import Optional, Dict, Any

import psycopg2
from psycopg2.extras import DictCursor

from logging_config import configure_logger
from env_config import env_config
from helpers import StatusFetchShazam

# Constants
BLOCKED_KEYWORDS_NOT_TO_REGISTER_SOUND_IN_DB = ["Arewa Trend Music", "DJ SU LAMA DEKAT",
                                                "Astercalm", "DJ MAS",
                                                "NY Latino Party Time",
                                                "Far Away - Juliane Wolf"]

logger = configure_logger()


def get_db_connection():
    return psycopg2.connect(env_config.database_url)


def extract_shazam_sound_id(url):
    match = re.search(r'(?:track|song)/(\d+)', url)
    return match.group(1) if match else None


def get_shazam_label_name(track_info: Dict[str, Any]) -> Optional[str]:
    sections = track_info.get('sections', [])

    if not sections:
        return None

    song_section = next((section for section in sections if section.get('type') == 'SONG'), None)

    if not song_section:
        return None

    metadata = song_section.get('metadata', [])

    if not metadata:
        return None

    # Find the metadata with title 'Label'
    label = next((meta for meta in metadata if meta.get('title') == 'Label'), {})

    # Get the text value from the label
    label_value = label.get('text', None)

    return label_value


def get_shazam_play_url(track_info: Dict[str, Any]) -> Optional[str]:
    hub_info = track_info.get('hub', {})
    actions = hub_info.get('actions', [])

    # Find the action with type 'uri' and 'uri' containing 'https://audio-ssl'
    for action in actions:
        if action.get('type') == 'uri' and 'https://audio-ssl' in action.get('uri', ''):
            return action.get('uri')
    return None


def get_existing_labels(cursor):
    query = 'SELECT id, name FROM public.sounds_data_labels'
    cursor.execute(query)

    labels = {}
    for record in cursor.fetchall():
        labels[record['name']] = record['id']

    return labels


def update_shazam_info(data):
    try:
        # Connect to postgres DB
        with get_db_connection() as conn:
            # Create a cursor object
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                existing_labels = get_existing_labels(cursor)

                success_count = 0
                failed_count = 0

                for item in data:
                    file_path = item.get('file', '')
                    tiktok_sound_id = os.path.splitext(os.path.basename(file_path))[0]

                    result = item.get('result', {})

                    track_info = result.get('track', {})
                    share_info = track_info.get('share', {})
                    images_info = track_info.get('images', {})

                    # Extract the values as specified
                    shazam_image_url = images_info.get('background', None)
                    shazam_name_of_sound = share_info.get('subject', None)
                    shazam_track_url = share_info.get('href', None)

                    shazam_label_name = get_shazam_label_name(track_info)
                    shazam_play_url = get_shazam_play_url(track_info)

                    # Extract Shazam sound ID from the URL
                    shazam_sound_id = extract_shazam_sound_id(shazam_track_url) if shazam_track_url else None

                    # Debug print statements
                    logger.info('file_path: %s\ntiktok_sound_id: %s', file_path, tiktok_sound_id)
                    logger.info('shazam_image_url: %s\nshazam_name_of_sound: %s\nshazam_track_url: %s',
                                shazam_image_url, shazam_name_of_sound, shazam_track_url)
                    logger.info('shazam_sound_id: %s\nshazam_label_name: %s\nshazam_play_url: %s',
                                shazam_sound_id, shazam_label_name, shazam_play_url)

                    # Check if any of the required fields are missing
                    if not all([shazam_image_url, shazam_name_of_sound, shazam_sound_id]):
                        logger.info('Missing required Shazam data, skipping insert.')
                        # Log missing items and continue to the next item

                        failed_count += 1
                        # Update tiktok_sound_last_checked_by_shazam_with_no_result if shazamsounds_id is None
                        update_query_no_result = """
                            UPDATE public.sounds_data_tiktoksounds
                            SET tiktok_sound_last_checked_by_shazam_with_no_result = 
                            CASE    WHEN (tiktok_sound_fetch_shazam_tries + 1) %% 3 = 0  
                                    THEN tiktok_sound_last_checked_by_shazam_with_no_result 
                                    ELSE %s
                            END,
                            tiktok_sound_fetch_shazam_tries = tiktok_sound_fetch_shazam_tries + 1,
                            tiktok_sound_fetch_shazam_status = 0
                            WHERE tiktok_sound_id = %s AND shazamsounds_id IS NULL;
                        """

                        cursor.execute(update_query_no_result, (datetime.now(), tiktok_sound_id))
                        continue

                    # Check if the result contains any of the specified keywords
                    if any(keyword in str(result) for keyword in BLOCKED_KEYWORDS_NOT_TO_REGISTER_SOUND_IN_DB):
                        update_query = """
                            UPDATE public.sounds_data_tiktoksounds
                            SET tiktok_sound_fetch_shazam_status = %s
                            WHERE tiktok_sound_id = %s;
                        """
                        cursor.execute(update_query, (StatusFetchShazam.BLOCKED_KEYWORDS, tiktok_sound_id))
                        logger.info(
                            'Skipping update for tiktok_sound_id %s due to blocked keyword match.', tiktok_sound_id)
                        continue

                    try:
                        shazamsounds_id = create_or_update_shazam_sound(
                            cursor, shazam_sound_id, shazam_image_url, shazam_name_of_sound, shazam_label_name,
                            shazam_play_url, existing_labels)

                        update_query = """
                            UPDATE public.sounds_data_tiktoksounds
                            SET shazamsounds_id = %s,
                                tiktok_sound_fetch_shazam_status = %s
                            WHERE tiktok_sound_id = %s;
                        """
                        cursor.execute(update_query, (shazamsounds_id, StatusFetchShazam.PROCESSED, tiktok_sound_id))
                        logger.info('Updated TikTok sound ID %s with Shazam sound ID %s.',
                                    tiktok_sound_id, shazamsounds_id)

                        success_count += 1
                    except Exception as ex:
                        logger.error('Error while updating Shazam info: %s', ex, exc_info=True)
                        failed_count += 1

                        continue

                # Commit the changes
                conn.commit()

                logger.info('Successfully updated %s TikTok sounds with Shazam info.', success_count)
                logger.info('Failed to update %s TikTok sounds with Shazam info.', failed_count)
    except Exception as e:
        logger.error('Error while updating Shazam info: %s', e, exc_info=True)


def get_or_create_label(cursor, label_name, existing_labels):
    if not label_name:
        return None

    label_id = existing_labels.get(label_name, None)

    if not label_id:
        # Insert the new label_name
        insert_query = """
            INSERT INTO public.sounds_data_labels (name, inserted)
            VALUES (%s, NOW())
            RETURNING id;
        """
        cursor.execute(insert_query, (label_name,))
        label_id = cursor.fetchone()[0]
        existing_labels[label_name] = label_id

    return label_id


def create_or_update_shazam_sound(
    cursor, shazam_sound_id, shazam_image_url, shazam_name_of_sound,
    shazam_label_name, shazam_play_url, existing_labels
):
    check_query = 'SELECT id, label_id FROM public.sounds_data_shazamsounds WHERE shazam_sound_id = %s;'
    cursor.execute(check_query, (shazam_sound_id,))
    existing_record = cursor.fetchone()

    label_id = get_or_create_label(cursor, shazam_label_name, existing_labels)

    if existing_record:
        shazamsounds_id, existing_label_id = existing_record

        if label_id != existing_label_id:
            update_query = """
                UPDATE  public.sounds_data_shazamsounds
                SET     label_id = %s
                WHERE   id = %s;
            """

            cursor.execute(update_query, (label_id, shazamsounds_id))
    else:
        # Insert into public.sounds_data_shazamsounds
        insert_query = """
            INSERT INTO public.sounds_data_shazamsounds (shazam_image_url, shazam_name_of_sound, shazam_sound_id, 
                        shazam_play_url, label_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """
        cursor.execute(insert_query, (shazam_image_url, shazam_name_of_sound,
                       shazam_sound_id, shazam_play_url, label_id))
        shazamsounds_id = cursor.fetchone()[0]

        logger.info('Inserted new Shazam sound ID %s with ID %s.', shazam_sound_id, shazamsounds_id)

    return shazamsounds_id


def clean_sounds_directory(directory_path):
    try:
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        logger.info('Cleaned all files in directory: %s', directory_path)
    except Exception as e:
        logger.error('Error while cleaning directory: %s', e, exc_info=True)


def analyse_shazam_api_response_json():
    logger.info('Start analyzing Shazam API response JSON')

    # Load the JSON data from the file with UTF-8 encoding
    shazam_api_response_path = env_config.shazam_api_response_path
    with open(shazam_api_response_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    update_shazam_info(data)

    with open(shazam_api_response_path, 'w', encoding='utf-8') as json_file:
        json.dump([], json_file)


if __name__ == '__main__':
    analyse_shazam_api_response_json()
