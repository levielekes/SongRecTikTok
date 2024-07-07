import os
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

# Define source and destination directories
source_dir = os.getenv('SOUNDS_DIR_FRONTEND_REFRESH_API')
destination_dir = os.getenv('SOUNDS_DIR_FRONTEND_REFRESH_API')

# Ensure the destination directory exists
os.makedirs(destination_dir, exist_ok=True)

# Convert non-MP3 files to MP3 and move them to the destination directory
for filename in os.listdir(source_dir):
    # Define the full path for the source file
    source_path = os.path.join(source_dir, filename)
    
    # Define the full path for the destination file
    base, ext = os.path.splitext(filename)
    destination_path = os.path.join(destination_dir, f"{base}.mp3")
    
    # Check if the file is not an MP3
    if ext.lower() != '.mp3':
        # Convert the file to MP3
        audio = AudioSegment.from_file(source_path)
        audio.export(destination_path, format='mp3')
        
        # Remove the original file
        os.remove(source_path)

print("Conversion complete and files moved.")
