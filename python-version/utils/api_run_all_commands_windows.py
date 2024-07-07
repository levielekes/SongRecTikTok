import subprocess

commands = [
    'python python-version/utils/api_script_which_complete_db.py',
    'python python-version/utils/api_convert_m4a_to_mp3.py',
    'python python-version/utils/api_audio_file_to_recognized_song.py',
    'python python-version/utils/api_analyse_shazam_api_response_json.py',
]

for command in commands:
    subprocess.run(command, shell=True)