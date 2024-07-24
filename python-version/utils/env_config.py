import os
from dotenv import load_dotenv


class EnvConfig:
    def __init__(self):
        load_dotenv()

        self._database_url = None
        self._download_dir = None
        self._shazam_api_response_path = None
        self._sounds_dir = None
        self._limit_tiktok_sounds_to_fetch = None

    @property
    def database_url(self):
        if self._database_url is None:
            self._database_url = os.getenv('DATABASE_URL')

            if not self._database_url:
                raise ValueError('DATABASE_URL environment variable not set')

        return self._database_url

    @property
    def download_dir(self):
        if self._download_dir is None:
            self._download_dir = os.getenv('SOUNDS_DIR', os.path.join(os.getcwd(), 'python-version/sounds'))

            os.makedirs(self._download_dir, exist_ok=True)

        return self._download_dir

    @property
    def shazam_api_response_path(self):
        if self._shazam_api_response_path is None:
            self._shazam_api_response_path = os.getenv('SHAZAM_API_RESPONSE_PATH')

            if not self._shazam_api_response_path:
                raise ValueError('SHAZAM_API_RESPONSE_PATH environment variable not set')

        return self._shazam_api_response_path

    @property
    def sounds_dir(self):
        if self._sounds_dir is None:
            self._sounds_dir = os.getenv('SOUNDS_DIR', os.path.join(os.getcwd(), 'python-version/sounds'))

            os.makedirs(self._sounds_dir, exist_ok=True)

        return self._sounds_dir

    @property
    def limit_tiktok_sounds_to_fetch(self):
        if self._limit_tiktok_sounds_to_fetch is None:
            self._limit_tiktok_sounds_to_fetch = os.getenv('TIKTOK_SOUNDS_TO_FETCH_LIMIT', '4000')

        return self._limit_tiktok_sounds_to_fetch


env_config = EnvConfig()
