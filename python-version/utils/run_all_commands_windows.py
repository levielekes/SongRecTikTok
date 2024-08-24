import time
import subprocess
from logging_config import configure_logger

logger = configure_logger()

commands = [
    'python python-version/utils/script_which_complete_db.py',
    'python python-version/utils/convert_m4a_to_mp3_and_cut_audio.py',
    'python python-version/utils/audio_file_to_recognized_song.py',
    'python python-version/utils/analyse_shazam_api_response_json.py',
]

def run_command(command):
    """Run a single command and handle errors."""
    try:
        subprocess.run(command, check=True, shell=True)
        logger.info('Command %s has been run', command)
    except subprocess.CalledProcessError as e:
        logger.error('Error running command %s: %s', command, e, exc_info=True)
        return False
    
    return True

def run_commands_indefinitely():
    logger.info('Start running all commands')
    
    while True:
        for command in commands:
            if not run_command(command):
                return
        
        logger.info('All commands have been run. Sleeping for 60 seconds')
        time.sleep(60)

if __name__ == '__main__':
    run_commands_indefinitely()