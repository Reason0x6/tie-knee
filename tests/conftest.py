import os
from pathlib import Path
import tempfile

os.environ["API_KEYS"] = "test-key"
os.environ["SHARE_BASE_URL"] = "https://tiny.vk2fgav.com"
os.environ["SHARE_DB_PATH"] = str(Path(tempfile.gettempdir()) / "text-utils-api-tests.db")
