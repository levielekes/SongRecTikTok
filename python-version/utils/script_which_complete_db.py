import os
import json
import psycopg2
import requests
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

from logging_config import configure_logger
# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

# Define the directory to save the downloaded files
DOWNLOAD_DIR = os.getenv('SOUNDS_DIR', os.path.join(os.getcwd(), 'python-version/sounds'))

# Create the directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

logger = configure_logger()


def fetch_tiktok_play_urls():
    download_results = []
    try:
        # Connect to the PostgreSQL database using the DATABASE_URL
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor(cursor_factory=DictCursor)  # Use DictCursor to fetch rows as dictionaries

        query = '''
        SELECT 
            tiktok_play_url, 
            tiktok_sound_id, 
            tiktok_sound_last_checked_by_shazam_with_no_result,
            shazamsounds_id,
            public.sounds_data_tiktoksoundidsdailytotalvideocount.tiktok_total_video_count,
            public.sounds_data_tiktoksoundidsdailytotalvideocount.date
        FROM 
            public.sounds_data_tiktoksounds 
        LEFT JOIN 
            public.sounds_data_shazamsounds 
        ON 
            public.sounds_data_tiktoksounds.shazamsounds_id = public.sounds_data_shazamsounds.id 
        LEFT JOIN (
            SELECT tiktoksounds_id, MAX(date) as max_date
            FROM public.sounds_data_tiktoksoundidsdailytotalvideocount
            GROUP BY tiktoksounds_id
        ) latest_v ON public.sounds_data_tiktoksounds.id = latest_v.tiktoksounds_id
        LEFT JOIN public.sounds_data_tiktoksoundidsdailytotalvideocount 
        ON 
            latest_v.tiktoksounds_id = public.sounds_data_tiktoksoundidsdailytotalvideocount.tiktoksounds_id 
            AND latest_v.max_date = public.sounds_data_tiktoksoundidsdailytotalvideocount.date
        WHERE
            public.sounds_data_tiktoksounds.status = 0
            AND (
                    (
                    public.sounds_data_tiktoksounds.shazamsounds_id IS NULL 
                    AND (
                        tiktok_sound_last_checked_by_shazam_with_no_result IS NULL 
                        OR tiktok_sound_last_checked_by_shazam_with_no_result <= current_date - INTERVAL '14 days'
                    )
                    AND public.sounds_data_tiktoksoundidsdailytotalvideocount.tiktok_total_video_count >= 50
                )
                OR 
                (
                    public.sounds_data_shazamsounds.label_id IS NULL
                    AND public.sounds_data_tiktoksoundidsdailytotalvideocount.tiktok_total_video_count >= 50
                )
            )
            LIMIT 4000
        '''
        cursor.execute(query)

        # Fetch all rows
        rows = cursor.fetchall()

        # Download each file and save it to the directory
        for row in rows:
            tiktok_play_url = row['tiktok_play_url']
            tiktok_sound_id = row['tiktok_sound_id']
            result = {'url': tiktok_play_url, 'status': 'success'}
            try:
                # Determine the file name based on the URL and tiktok_sound_id
                if tiktok_play_url.endswith('.mp3'):
                    file_name = f'{tiktok_sound_id}.mp3'
                else:
                    file_extension = os.path.splitext(tiktok_play_url)[1]
                    file_name = f'{tiktok_sound_id}{file_extension}'

                file_path = os.path.join(DOWNLOAD_DIR, file_name)

                # Download the file
                response = requests.get(tiktok_play_url)
                response.raise_for_status()

                # Save the file to the specified directory
                with open(file_path, 'wb') as file:
                    file.write(response.content)

                result['file_path'] = file_path

                # Print the tiktok_play_url to the terminal
                logger.info('Downloaded: %s', tiktok_play_url)
            except Exception as download_error:
                result['status'] = 'error'
                result['error_message'] = str(download_error)
                logger.error('Error downloading %s: %s', tiktok_play_url, download_error, exc_info=True)
            finally:
                download_results.append(result)

    except Exception as error:
        logger.error('Error fetching data: %s', error, exc_info=True)
    finally:
        if connection:
            cursor.close()
            connection.close()

    # Save results to a JSON file
    json_file_path = os.path.join(os.getcwd(), 'download_results.json')
    with open(json_file_path, 'w', encoding='UTF-8') as json_file:
        json.dump(download_results, json_file, indent=4)


if __name__ == '__main__':
    fetch_tiktok_play_urls()
