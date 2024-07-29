import os
from dotenv import load_dotenv


class EnvConfig:
    def __init__(self):
        load_dotenv()

        self._config = {}
        self._download_dir = None

    def _get_env_var(self, var_name, default=None, required=False, cast_type=str):
        """Retrieve and cache environment variables."""
        if var_name not in self._config:
            value = os.getenv(var_name, default)

            if required and not value:
                raise ValueError(f'{var_name} environment variable not set')
            self._config[var_name] = cast_type(value) if value else value

        return self._config[var_name]

    @property
    def database_url(self):
        return self._get_env_var('DATABASE_URL', required=True)

    @property
    def download_dir(self):
        if self._download_dir is None:
            self._download_dir = os.getenv('SOUNDS_DIR', os.path.join(os.getcwd(), 'python-version/sounds'))

            os.makedirs(self._download_dir, exist_ok=True)

        return self._download_dir

    @property
    def shazam_api_response_path(self):
        return self._get_env_var('SHAZAM_API_RESPONSE_PATH', required=True)

    @property
    def limit_tiktok_sounds_to_fetch(self):
        return self._get_env_var('TIKTOK_SOUNDS_TO_FETCH_LIMIT', 4000, cast_type=int)

    @property
    def max_requests_before_rate_limit_reached(self):
        return self._get_env_var('SHAZAM_MAX_REQUESTS_BEFORE_RATE_LIMIT_REACHED', 5, cast_type=int)

    @property
    def sleep_time_after_rate_limit_reached(self):
        return self._get_env_var('SHAZAM_SLEEP_TIME_AFTER_RATE_LIMIT_REACHED', 60, cast_type=int)


env_config = EnvConfig()
