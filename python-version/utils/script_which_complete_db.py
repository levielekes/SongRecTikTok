import os
from enum import IntEnum
import psycopg2
import requests

from psycopg2.extras import DictCursor
from env_config import env_config
from logging_config import configure_logger


logger = configure_logger()


class StatusFetchShazam(IntEnum):
    NOT_FETCHED = 0
    IN_PROGRESS = 1
    DOWNLOADED = 2


def update_tiktok_sound_fetch_shazam_status(connection, cursor: DictCursor, tiktok_sound_id: int, status: int):
    try:
        query = '''
        UPDATE sounds_data_tiktoksounds
        SET tiktok_sound_fetch_shazam_status = %s
        WHERE id = %s;
        '''
        cursor.execute(query, (status, tiktok_sound_id))
        connection.commit()
    except Exception as error:
        logger.error('Error updating data: %s', error, exc_info=True)


def fetch_tiktok_play_urls():
    try:
        # Connect to the PostgreSQL database using the DATABASE_URL
        with psycopg2.connect(env_config.database_url) as connection:
            # Create a new cursor using DictCursor to return rows as dictionaries
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                query = '''
                UPDATE sounds_data_tiktoksounds
                SET tiktok_sound_fetch_shazam_status = %s
                WHERE id IN (
                    SELECT 
                        sounds_data_tiktoksounds.id
                    FROM 
                        sounds_data_tiktoksounds 
                    LEFT JOIN 
                        sounds_data_shazamsounds 
                    ON 
                        sounds_data_tiktoksounds.shazamsounds_id = sounds_data_shazamsounds.id 
                    WHERE
                        sounds_data_tiktoksounds.tiktok_sound_fetch_shazam_status = 0
                        AND sounds_data_tiktoksounds.status = 0
                        AND sounds_data_tiktoksounds.shazamsounds_id IS NULL 
                        AND (
                            tiktok_sound_last_checked_by_shazam_with_no_result IS NULL 
                            OR tiktok_sound_last_checked_by_shazam_with_no_result <= current_date - INTERVAL '10 days'
                        )                                          
                    ORDER BY sounds_data_tiktoksounds.tiktok_total_video_count DESC
                    LIMIT %s
                )
                RETURNING id, tiktok_play_url, tiktok_sound_id;
                '''

                cursor.execute(query, (StatusFetchShazam.IN_PROGRESS, env_config.limit_tiktok_sounds_to_fetch,))
                connection.commit()
                # Fetch all rows
                rows = cursor.fetchall()

                # Download each file and save it to the directory
                for row in rows:
                    tiktoksounds_id = row['id']
                    tiktok_play_url = row['tiktok_play_url']
                    tiktok_sound_id = row['tiktok_sound_id']

                    try:
                        # Determine the file name based on the URL and tiktok_sound_id
                        if tiktok_play_url.endswith('.mp3'):
                            file_name = f'{tiktok_sound_id}.mp3'
                        else:
                            file_extension = os.path.splitext(tiktok_play_url)[1]
                            file_name = f'{tiktok_sound_id}{file_extension}'

                        file_path = os.path.join(env_config.download_dir, file_name)

                        # Download the file
                        response = requests.get(tiktok_play_url, timeout=60)
                        response.raise_for_status()

                        # Save the file to the specified directory
                        with open(file_path, 'wb') as file:
                            file.write(response.content)

                        # Print the tiktok_play_url to the terminal
                        logger.info('Downloaded: %s', tiktok_play_url)
                        update_tiktok_sound_fetch_shazam_status(
                            connection, cursor, tiktoksounds_id, StatusFetchShazam.DOWNLOADED)
                    except Exception as download_error:
                        logger.error('Error downloading %s: %s', tiktok_play_url, download_error, exc_info=True)
                        update_tiktok_sound_fetch_shazam_status(
                            connection, cursor, tiktoksounds_id, StatusFetchShazam.NOT_FETCHED)

    except Exception as error:
        logger.error('Error fetching data: %s', error, exc_info=True)


if __name__ == '__main__':
    fetch_tiktok_play_urls()