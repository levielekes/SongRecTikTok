import json
import os
import re
import time

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
                                                "Far Away - Juliane Wolf",
                                                "Airflow - MegaPower",
                                                "Amurai Remix Amurai's los Angeles Mix",
                                                "Learning to Fly (Mike Koglin Remix) - Mothers Pride",
                                                "Toccata and Fugue In D Minor, BWV 565 - Miklós Spányi & Silbermann"
                                                "We Are Mirage - Eric Prydz & Empire Of The Sun"
                                                "Apollo - Thomas Schumacher & Victor Ruiz"
                                                ]

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


def extract_track_info(result):
    track_info = result.get('track', {})
    share_info = track_info.get('share', {})
    images_info = track_info.get('images', {})
    shazam_track_url = share_info.get('href', None)

    return {
        'shazam_image_url': images_info.get('background', None),
        'shazam_name_of_sound': share_info.get('subject', None),
        'shazam_track_url': shazam_track_url,
        'shazam_label_name': get_shazam_label_name(track_info),
        'shazam_play_url': get_shazam_play_url(track_info),
        'shazam_sound_id': extract_shazam_sound_id(shazam_track_url) if shazam_track_url else None
    }


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
                    retries = 0
                    while retries < 3:
                        try:
                            success, error_message = process_shazam_item(item, cursor, existing_labels)
                            conn.commit()

                            if success:
                                success_count += 1
                            else:
                                logger.info('Failed to process item: %s', error_message)
                                failed_count += 1

                            break  # Exit retry while if succesfull
                        except psycopg2.OperationalError as ex:
                            conn.rollback()

                            if 'deadlock detected' in str(ex):
                                logger.info('Retrying deadlock detected operation after %s seconds', retries * 5)
                                retries += 1
                                time.sleep(retries * 2)
                            else:
                                logger.error('Error while running query to update shazam: %s', ex, exc_info=True)
                                failed_count += 1
                                break
                        except Exception as ex:
                            conn.rollback()
                            logger.error('Error while updating Shazam info: %s', ex, exc_info=True)
                            failed_count += 1
                            break  # Exit retry while for general errors

                logger.info('Successfully updated %s TikTok sounds with Shazam info.', success_count)
                logger.info('Failed to update %s TikTok sounds with Shazam info.', failed_count)
    except Exception as e:
        logger.error('Error while running analyse shazam response: %s', e, exc_info=True)


def process_shazam_item(item, cursor, existing_labels):
    file_path = item.get('file', '')
    tiktok_sound_id = os.path.splitext(os.path.basename(file_path))[0]

    result = item.get('result', {})
    track_info = extract_track_info(result)
    error = result.get('error', '')

    # Debug print statements
    logger.info('file_path: %s\ntiktok_sound_id: %s', file_path, tiktok_sound_id)
    logger.info('shazam_image_url: %s\nshazam_name_of_sound: %s\nshazam_track_url: %s',
                track_info['shazam_image_url'], track_info['shazam_name_of_sound'],
                track_info['shazam_track_url'])
    logger.info('shazam_sound_id: %s\nshazam_label_name: %s\nshazam_play_url: %s',
                track_info['shazam_sound_id'], track_info['shazam_label_name'],
                track_info['shazam_play_url'])

    if error:
        update_query_error = """
            UPDATE  sounds_data_tiktoksounds
            SET     tiktok_sound_shazam_error = %s,
                    tiktok_sound_fetch_shazam_status = 0
            WHERE   tiktok_sound_id = %s"""

        cursor.execute(update_query_error, (error, tiktok_sound_id))
        return False, f'Error found: {error}'

    # Check if any of the required fields are missing
    if not all([track_info['shazam_name_of_sound'], track_info['shazam_sound_id']]):
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
        return False, 'Missing required Shazam data, skipping update'

    # Check if the result contains any of the specified keywords
    if any(keyword in str(result) for keyword in BLOCKED_KEYWORDS_NOT_TO_REGISTER_SOUND_IN_DB):
        update_query = """
            UPDATE public.sounds_data_tiktoksounds
            SET tiktok_sound_fetch_shazam_status = %s
            WHERE tiktok_sound_id = %s;
        """
        cursor.execute(update_query, (StatusFetchShazam.BLOCKED_KEYWORDS, tiktok_sound_id))
        return False, 'Blocked keywords found'

    shazamsounds_id = create_or_update_shazam_sound(cursor, track_info, existing_labels)

    update_query = """
        UPDATE public.sounds_data_tiktoksounds
        SET shazamsounds_id = %s,
            tiktok_sound_fetch_shazam_status = %s,
            tiktok_sound_shazam_error = ''
        WHERE tiktok_sound_id = %s;
    """
    cursor.execute(update_query, (shazamsounds_id, StatusFetchShazam.PROCESSED, tiktok_sound_id))
    logger.info('Updated TikTok sound ID %s with Shazam sound ID %s.',
                tiktok_sound_id, shazamsounds_id)

    return True, None


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


def create_or_update_shazam_sound(cursor, track_info, existing_labels):
    check_query = 'SELECT id, label_id FROM public.sounds_data_shazamsounds WHERE shazam_sound_id = %s;'
    cursor.execute(check_query, (track_info['shazam_sound_id'],))
    existing_record = cursor.fetchone()

    label_id = get_or_create_label(cursor, track_info['shazam_label_name'], existing_labels)

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
        cursor.execute(insert_query, (track_info['shazam_image_url'], track_info['shazam_name_of_sound'],
                       track_info['shazam_sound_id'], track_info['shazam_play_url'], label_id))
        shazamsounds_id = cursor.fetchone()[0]

        logger.info('Inserted new Shazam sound ID %s with ID %s.', track_info['shazam_sound_id'], shazamsounds_id)

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
