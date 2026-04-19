from functools import lru_cache
import os


class Settings:
    def __init__(self) -> None:
        raw_api_keys = os.getenv("API_KEYS", "")
        self.api_keys = {
            key.strip()
            for key in raw_api_keys.split(",")
            if key.strip()
        }
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.log_level = os.getenv("LOG_LEVEL", "info")
        self.share_base_url = os.getenv("SHARE_BASE_URL", "https://tiny.vk2fgav.com").rstrip("/")
        self.share_db_path = os.getenv("SHARE_DB_PATH", "./data/text-utils.db")


@lru_cache
def get_settings() -> Settings:
    return Settings()
