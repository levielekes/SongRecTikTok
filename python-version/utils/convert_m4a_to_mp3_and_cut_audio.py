import os
import os.path
import tempfile
from pydub import AudioSegment
from pyffmpeg import FFmpeg
from logging_config import configure_logger
from env_config import env_config

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
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_path = temp_file.name
    
    filter_complex = f"[0:a]adelay=0|{delay_ms}[aout]"
    ff.options(
        f'-i "{input_file}" -filter_complex "{filter_complex}" -map "[aout]" "{temp_path}"'
    )
    
    # Move the temp file to the output file
    os.replace(temp_path, output_file)

def convert_to_mp3(input_file, output_file):
    """Convert audio file to MP3 format."""
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format='mp3')
    logger.info(f"Converted {input_file} to MP3")

# Main processing loop
for filename in os.listdir(env_config.download_dir):
    # Define the full path for the source file
    source_path = os.path.join(env_config.download_dir, filename)
    
    # Define the base name and extension
    base, ext = os.path.splitext(filename)
    
    logger.info('Processing file: %s', filename)
    
    # Step 1: Convert to MP3 if not already in MP3 format
    if ext.lower() != '.mp3':
        destination_path = os.path.join(env_config.download_dir, f"{base}.mp3")
        convert_to_mp3(source_path, destination_path)
        # Remove the original file after conversion
        os.remove(source_path)
    else:
        destination_path = source_path

    # Step 2: Load the audio file (converted or original mp3)
    audio = AudioSegment.from_file(destination_path)

    # Step 3: Process audio (repeat and trim)
    processed_audio = process_audio(audio)

    # Step 4: Export the processed audio to a temp file
    processed_path = os.path.join(env_config.download_dir, f"{base}_processed.mp3")
    processed_audio.export(processed_path, format='mp3')

    # Step 5: Apply audio delay to the processed audio
    delayed_path = os.path.join(env_config.download_dir, f"{base}_delayed.mp3")
    apply_audio_delay(processed_path, delayed_path, DELAY_MS)

    # Step 6: Move the delayed file to the final destination (overwrite destination_path)
    os.replace(delayed_path, destination_path)

    # Step 7: Remove the temporary processed file
    os.remove(processed_path)

logger.info('Processing complete and files moved.')