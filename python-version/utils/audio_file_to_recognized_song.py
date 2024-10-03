#!/usr/bin/python3
# -*- encoding: Utf-8 -*-
import os
import sys
import json
import time

from json import dumps
from os.path import dirname, realpath, join
from pydub import AudioSegment

from logging_config import configure_logger
from env_config import env_config

UTILS_DIR = realpath(dirname(__file__))
SCRIPT_DIR = dirname(realpath(__file__))
ROOT_DIR = realpath(SCRIPT_DIR + '/..')
FINGERPRINTING_DIR = realpath(ROOT_DIR + '/fingerprinting')

sys.path.append(FINGERPRINTING_DIR)
from algorithm import SignatureGenerator
from communication import recognize_song_from_signature


logger = configure_logger()


class RateLimiter:
    def __init__(self, max_requests_per_unit=env_config.max_requests_before_rate_limit_reached):
        self.max_requests_per_unit = max_requests_per_unit
        self.current_requests = 0
        self.max_time_unit = env_config.sleep_time_after_rate_limit_reached

    def increment(self):
        self.current_requests += 1
        if self.current_requests >= self.max_requests_per_unit:
            logger.info('Rate limit reached, waiting for %s seconds...', self.max_time_unit)
            time.sleep(self.max_time_unit)
            self.current_requests = 0

    def reset(self):
        self.current_requests = 0


def preprocess_audio(audio):
    audio = audio.set_sample_width(2)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_channels(1)
    return audio


def recognize(signature_generator, rate_limiter):
    results = '(Not enough data)'

    while True:
        signature = signature_generator.get_next_signature()
        if not signature:
            break

        results = recognize_song_from_signature(signature)
        rate_limiter.increment()

        if results.get('error', None):
            status_code = results.get('status_code', None)
            if status_code == 429:
                logger.info('Rate limit reached because 429 too many requests, waiting for %s seconds...',
                            rate_limiter.max_time_unit)

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
            time.sleep(retry_time_ms / 1000)
        else:
            logger.info('[Note: No matching songs for the first %g seconds, trying to recognize more input... ]',
                        signature_generator.samples_processed / 16000)

    return results


def process_audio_file(file_path: str, rate_limiter: RateLimiter):
    try:
        audio = AudioSegment.from_file(file_path)
        audio_processed = preprocess_audio(audio)

        logger.info("Running recognition attempt...")
        signature_generator = SignatureGenerator()
        signature_generator.feed_input(audio_processed.get_array_of_samples())
        signature_generator.MAX_TIME_SECONDS = 16
        results = recognize(signature_generator, rate_limiter)

        return file_path, results

    except Exception as e:
        logger.error('Error processing file %s: %s', file_path, e, exc_info=True)
        return file_path, {"error": str(e)}


def main():
    json_output_path = env_config.shazam_api_response_path

    if not os.path.exists(json_output_path):
        with open(json_output_path, 'w', encoding='utf-8') as json_file:
            json.dump([], json_file)

    rate_limiter = RateLimiter()

    for file_name in os.listdir(env_config.download_dir):
        if file_name.endswith('.wav') or file_name.endswith('.mp3'):
            file_path = join(env_config.download_dir, file_name)
            logger.info('Processing file: %s', file_path)

            file_path, result = process_audio_file(file_path, rate_limiter)

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
