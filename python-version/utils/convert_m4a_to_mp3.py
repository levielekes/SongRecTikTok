import os
from pydub import AudioSegment
from logging_config import configure_logger
from env_config import env_config

logger = configure_logger()

def trim_audio(audio, max_duration_ms=14000):
    """Trim audio to the specified duration if it's longer."""
    if len(audio) > max_duration_ms:
        return audio[:max_duration_ms]
    return audio

# Convert non-MP3 files to MP3, trim if necessary, and move them to the destination directory
for filename in os.listdir(env_config.download_dir):
    # Define the full path for the source file
    source_path = os.path.join(env_config.download_dir, filename)

    # Define the full path for the destination file
    base, ext = os.path.splitext(filename)
    destination_path = os.path.join(env_config.download_dir, f"{base}.mp3")

    logger.info('Processing file: %s', filename)
    
    # Load the audio file
    audio = AudioSegment.from_file(source_path)
    
    # Trim the audio if it's longer than 14 seconds
    audio = trim_audio(audio)
    
    # Export as MP3
    audio.export(destination_path, format='mp3')

    # Remove the original file if it's not already an MP3
    if ext.lower() != '.mp3':
        os.remove(source_path)

logger.info('Processing complete and files moved.')