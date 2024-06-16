import os
from pydub import AudioSegment

# Define source and destination directories
source_dir = '/repos/SongRecTikTok/python-version/sounds'
destination_dir = '/repos/SongRecTikTok/python-version/sounds'

# Ensure the destination directory exists
os.makedirs(destination_dir, exist_ok=True)

# Convert m4a files to mp3 and move them to the destination directory
for filename in os.listdir(source_dir):
    if filename.endswith('.m4a'):
        # Define the full path for the source file
        source_path = os.path.join(source_dir, filename)
        
        # Define the full path for the destination file
        base = os.path.splitext(filename)[0]
        destination_path = os.path.join(destination_dir, f"{base}.mp3")
        
        # Convert m4a to mp3
        audio = AudioSegment.from_file(source_path, format='m4a')
        audio.export(destination_path, format='mp3')
        
        # Remove the original m4a file
        os.remove(source_path)

print("Conversion complete and files moved.")