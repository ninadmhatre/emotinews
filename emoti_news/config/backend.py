from typing import Any
import os

NEWS_SOURCE = "newsapi"
SOURCE_API_KEY = {
    "newsapi.org": os.getenv("API_NEWSAPI_ORG"),
    "newsdata.io": os.getenv("API_NEWSDATA_IO"),
}

# Cache configuration
CACHE_CONFIG: dict[str, Any] = {
    "enable": 1,  # 1 to enable, 0 to disable
    "dir": "/tmp/enews",  # Cache directory
    "ttl": 180,  # Time to live in minutes
    "refresh": 0,  # 1 to force refresh, 0 to use cache if valid
}
