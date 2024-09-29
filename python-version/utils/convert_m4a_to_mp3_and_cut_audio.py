import os
import os.path
import time
import tempfile
from pydub import AudioSegment
from pydub.utils import which
from pyffmpeg import FFmpeg
from logging_config import configure_logger
from env_config import env_config
import mutagen

# Configure pydub to use FFmpeg
AudioSegment.converter = which("ffmpeg")

logger = configure_logger()
DELAY_MS = 200
ff = FFmpeg()

def trim_audio(audio, max_duration_ms=14000):
    """Trim audio to the specified duration if it's longer."""
    if len(audio) > max_duration_ms:
        return audio[:max_duration_ms]
    return audio

def process_audio(audio, target_duration_ms=14000):
    """
    Process the audio to meet the specified requirements:
    1. If shorter than target duration, repeat until reaching or exceeding it.
    2. Trim to exactly target duration.
    """
    current_duration = len(audio)
    # Step 1: Repeat audio if it's shorter than target duration
    if current_duration < target_duration_ms:
        repetitions = target_duration_ms // current_duration + 1
        audio = audio * repetitions
    
    # Step 2: Trim to exactly target duration
    return trim_audio(audio, target_duration_ms)

def apply_audio_delay(input_file, output_file, delay_ms):
    start_time = time.time()
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_path = temp_file.name
    
    filter_complex = f"[0:a]adelay=0|{delay_ms}[aout]"
    command = f'-i "{input_file}" -filter_complex "{filter_complex}" -map "[aout]" "{temp_path}"'
    
    try:
        result = ff.options(command)
        if hasattr(result, 'stderr') and result.stderr:
            logger.warning(f"FFmpeg stderr: {result.stderr}")
        if hasattr(result, 'returncode') and result.returncode != 0:
            raise Exception(f"FFmpeg command failed with return code {result.returncode}")
    except Exception as e:
        logger.error(f"Error applying audio delay: {str(e)}")
        return False
    
    # Move the temp file to the output file
    os.replace(temp_path, output_file)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Audio delay applied in {elapsed_time:.2f} seconds")
    return True

def get_audio_info(file_path):
    audio = mutagen.File(file_path)
    if audio is None:
        raise ValueError(f"Could not load audio file: {file_path}")
    
    channels = audio.info.channels
    sample_width = 2  # Assume 16-bit audio
    frame_rate = audio.info.sample_rate
    duration_seconds = audio.info.length
    return channels, sample_width, frame_rate, duration_seconds

def load_audio(file_path):
    channels, sample_width, frame_rate, duration_seconds = get_audio_info(file_path)
    return AudioSegment.from_mp3(file_path)

# Main processing loop
for filename in os.listdir(env_config.download_dir):
    # Define the full path for the source file
    source_path = os.path.join(env_config.download_dir, filename)
    
    # Define the full path for the destination file
    base, ext = os.path.splitext(filename)
    destination_path = os.path.join(env_config.download_dir, f"{base}.mp3")
    
    logger.info('Processing file: %s', filename)
    # Step 1: Apply audio delay
    if not apply_audio_delay(source_path, destination_path, DELAY_MS):
        logger.error(f"Skipping file {filename} due to error in apply_audio_delay")
        continue
    
    # Step 2: Load the delayed audio file
    try:
        audio = load_audio(destination_path)
    except Exception as e:
        logger.error(f"Error loading audio file {destination_path}: {str(e)}")
        continue
    
    # Step 3: Process audio (repeat and trim)
    processed_audio = process_audio(audio)
    
    # Step 4: Export as MP3 (overwriting the delayed file)
    try:
        processed_audio.export(destination_path, format='mp3')
    except Exception as e:
        logger.error(f"Error exporting processed audio {destination_path}: {str(e)}")
        continue
    
    # Step 5: Remove the original file if it's not already an MP3
    if ext.lower() != '.mp3' and source_path != destination_path:
        try:
            os.remove(source_path)
        except Exception as e:
            logger.error(f"Error removing original file {source_path}: {str(e)}")

logger.info('Processing complete and files moved.')