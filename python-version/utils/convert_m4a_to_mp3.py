import os
from pydub import AudioSegment
from logging_config import configure_logger
from env_config import env_config


logger = configure_logger()

# Convert non-MP3 files to MP3 and move them to the destination directory
for filename in os.listdir(env_config.download_dir):
    # Define the full path for the source file
    source_path = os.path.join(env_config.download_dir, filename)

    # Define the full path for the destination file
    base, ext = os.path.splitext(filename)
    destination_path = os.path.join(env_config.download_dir, f"{base}.mp3")

    logger.info('Converting file to MP3: %s', filename)
    # Check if the file is not an MP3
    if ext.lower() != '.mp3':
        # Convert the file to MP3
        audio = AudioSegment.from_file(source_path)
        audio.export(destination_path, format='mp3')

        # Remove the original file
        os.remove(source_path)

logger.info('Conversion complete and files moved.')
