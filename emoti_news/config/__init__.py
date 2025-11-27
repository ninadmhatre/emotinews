import os
import dataclasses
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parent.parent


@dataclasses.dataclass(frozen=True)
class CacheConfig:
    CacheDir: str = os.getenv("EMONEWS_CACHE_DIR", "/tmp/enews")
    TTL: int = int(os.getenv("EMONEWS_CACHE_TTL", "9600"))
    Enabled: bool = bool(os.getenv("EMONEWS_CACHE_ENABLED", "0"))
    Refresh: bool = bool(os.getenv("EMONEWS_CACHE_REFRESH", "0"))
