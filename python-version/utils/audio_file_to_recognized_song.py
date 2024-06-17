#!/usr/bin/python3
# -*- encoding: Utf-8 -*-
import os
import sys
import json
import time
from numpy import array as nparray, sin, pi, arange, concatenate
from os.path import dirname, realpath, join
from argparse import ArgumentParser
from pydub import AudioSegment
from sys import stderr
from json import dumps

UTILS_DIR = realpath(dirname(__file__))
SCRIPT_DIR = dirname(realpath(__file__))
ROOT_DIR = realpath(SCRIPT_DIR + '/..')
FINGERPRINTING_DIR = realpath(ROOT_DIR + '/fingerprinting')

sys.path.append(FINGERPRINTING_DIR)

from communication import recognize_song_from_signature
from algorithm import SignatureGenerator

# Correct SOUNDS_DIR path
SOUNDS_DIR = join(ROOT_DIR, 'sounds')

def process_audio_file(file_path):
    try:
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_sample_width(2)
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)

        signature_generator = SignatureGenerator()
        signature_generator.feed_input(audio.get_array_of_samples())

        signature_generator.MAX_TIME_SECONDS = 12
        if audio.duration_seconds > 12 * 3:
            signature_generator.samples_processed += 16000 * (int(audio.duration_seconds / 2) - 6)

        results = '(Not enough data)'

        while True:
            signature = signature_generator.get_next_signature()
            if not signature:
                break

            results = recognize_song_from_signature(signature)
            if results['matches']:
                break
            else:
                stderr.write(('[ Note: No matching songs for the first %g seconds, ' +
                              'trying to recognize more input... ]\n') % (signature_generator.samples_processed / 16000))
                stderr.flush()

        return file_path, results

    except Exception as e:
        return file_path, {"error": str(e)}

def main():
    all_results = []

    for file_name in os.listdir(SOUNDS_DIR):
        if file_name.endswith('.wav') or file_name.endswith('.mp3'):
            file_path = join(SOUNDS_DIR, file_name)
            print(f"Processing {file_path}")
            file_path, result = process_audio_file(file_path)
            all_results.append({"file": file_path, "result": result})

            # Sleep for 15 seconds to avoid rate limit
            time.sleep(15)

    json_output_path = join(SCRIPT_DIR, 'shazam_api_response.json')
    with open(json_output_path, 'w', encoding='utf-8') as json_file:
        json.dump(all_results, json_file, indent=4, ensure_ascii=False)

    print(f"All results have been saved to {json_output_path}")

if __name__ == '__main__':
    main()
