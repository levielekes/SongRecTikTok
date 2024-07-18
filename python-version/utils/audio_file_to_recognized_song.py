#!/usr/bin/python3
# -*- encoding: Utf-8 -*-
import os
import sys
import json
import time

from json import dumps
from os.path import dirname, realpath, join
from pydub import AudioSegment

from dotenv import load_dotenv
from logging_config import configure_logger

UTILS_DIR = realpath(dirname(__file__))
SCRIPT_DIR = dirname(realpath(__file__))
ROOT_DIR = realpath(SCRIPT_DIR + '/..')
FINGERPRINTING_DIR = realpath(ROOT_DIR + '/fingerprinting')

sys.path.append(FINGERPRINTING_DIR)
from algorithm import SignatureGenerator
from communication import recognize_song_from_signature


load_dotenv()

logger = configure_logger()

# Correct SOUNDS_DIR path
SOUNDS_DIR = os.getenv('SOUNDS_DIR', join(ROOT_DIR, 'sounds'))
MAX_REQUESTS_PER_UNIT_OF_TIME = 5


class RateLimiter:
    def __init__(self, max_requests_per_unit=MAX_REQUESTS_PER_UNIT_OF_TIME):
        self.max_requests_per_unit = max_requests_per_unit
        self.current_requests = 0
        self.max_time_unit = 60

    def increment(self):
        self.current_requests += 1
        if self.current_requests >= self.max_requests_per_unit:
            logger.info('Rate limit reached, waiting for %s seconds...', self.max_time_unit)
            time.sleep(self.max_time_unit)
            self.current_requests = 0

    def reset(self):
        self.current_requests = 0

def process_audio_file(file_path: str, rate_limiter: RateLimiter):
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
            rate_limiter.increment()

            signature = signature_generator.get_next_signature()
            if not signature:
                break

            results = recognize_song_from_signature(signature)

            if results.get('error', None):
                status_code = results.get('status_code', None)
                if status_code == 429:
                    logger.info('Rate limit reached, waiting for %s seconds...', rate_limiter.max_time_unit)
                    logger.info('Results: %s', dumps(results, indent=4, ensure_ascii=False))
                    time.sleep(rate_limiter.max_time_unit)
                    rate_limiter.reset()
                    continue
                else:
                    logger.error('Error recognizing song: %s', results['error'])
                    break

            if results.get('matches', []):
                break

            if results.get('retryms', None):
                retry_time_ms = results['retryms']
                logger.info('[Note: No matching songs found, retrying in %d ms...]', retry_time_ms)
                logger.info('Results: %s', dumps(results, indent=4, ensure_ascii=False))
                # Convert ms to seconds
                time.sleep(retry_time_ms / 1000)

                rate_limiter.increment()
                results = recognize_song_from_signature(signature)

                if results.get('error', None):
                    logger.error('Error recognizing song: %s', results['error'])
                    break
                if results.get('matches', []):
                    break
            else:
                logger.info('[Note: No matching songs for the first %g seconds, trying to recognize more input... ]',
                            signature_generator.samples_processed / 16000)
                logger.info('Results: %s', dumps(results, indent=4, ensure_ascii=False))

        return file_path, results

    except Exception as e:
        logger.error('Error processing file %s: %s', file_path, e, exc_info=True)
        return file_path, {"error": str(e)}


def main():
    json_output_path = os.getenv('SHAZAM_API_RESPONSE_PATH', join(SCRIPT_DIR, 'shazam_api_response.json'))

    # Clean the JSON file by opening it in write mode and closing it immediately
    with open(json_output_path, 'w', encoding='utf-8') as json_file:
        json.dump([], json_file)

    rate_limiter = RateLimiter()

    for file_name in os.listdir(SOUNDS_DIR):
        if file_name.endswith('.wav') or file_name.endswith('.mp3'):
            file_path = join(SOUNDS_DIR, file_name)
            logger.info('Processing file: %s', file_path)

            file_path, result = process_audio_file(file_path, rate_limiter)

            # Write the result to the JSON file immediately
            with open(json_output_path, 'r+', encoding='utf-8') as json_file:
                all_results = json.load(json_file)
                all_results.append({"file": file_path, "result": result})
                json_file.seek(0)
                json.dump(all_results, json_file, indent=4, ensure_ascii=False)
                json_file.truncate()

            os.remove(file_path)

    logger.info('All results have been saved to %s', json_output_path)


if __name__ == '__main__':
    main()
