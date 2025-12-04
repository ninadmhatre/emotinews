# Create a context manager CaptureCallStatus & TimeIt
import datetime as dt
import functools
import hashlib
import json
import pprint
import time
import types
from inspect import signature
from base64 import b64decode
from typing import Any, Dict, Optional, Callable, Type, Union

from diskcache import Cache
from sqlalchemy import text, inspect

from emoti_news.config import CacheConfig
from emoti_news.database.dal import add_new_status, update_status
from emoti_news.dtypes import JobStatus
from emoti_news.loggers import backend_logger as log

__all__ = ["CaptureCallStatus", "TimeIt", "dcache", "get_dcache"]


class CaptureCallStatus:
    def __init__(self, country: str, category: str) -> None:
        self.country: str = country
        self.category: str = category

        now: dt.datetime = dt.datetime.now()
        self.run_date: dt.date = now.date()
        self.hour_min: str = now.strftime("%H:%M")

        self.meta: Dict[str, Union[str, int, float, None]] = {
            "elapsed_time": None,
            "error": None,
            "rows_fetched": 0,
        }
        self.job_id: str = self._get_job_id()

    def _get_job_id(self) -> str:
        return f"{self.country}.{self.category}_{self.run_date.strftime('%Y%m%d')}_{self.hour_min}"

    def __enter__(self) -> "CaptureCallStatus":
        self.set_status(JobStatus.IN_PROGRESS)
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> bool:
        if exc_type is not None:
            # If there was an exception, mark as failed
            self.meta["error"] = str(exc_val) if exc_val else None
            self.update_status(JobStatus.FAILED)
        else:
            # If no exception, mark as completed
            self.update_status(JobStatus.COMPLETED)
        return False

    def set_meta(self, **kwargs: Any) -> None:
        self.meta = kwargs

    def set_status(self, status: Union[JobStatus, str]) -> None:
        """Insert a new status record"""
        status = status.value if isinstance(status, JobStatus) else status

        status_record: dict[str, Any] = {
            "job_id": self.job_id,
            "run_date": self.run_date,
            "hour_min": self.hour_min,
            "status": status.upper(),
            "meta": self.meta,
        }

        add_new_status(status_record)

    def update_status(self, status: JobStatus | str):
        """Update an existing status record"""
        return update_status(self.job_id, self.run_date, self.hour_min, self.meta, status)


class TimeIt:
    """A context manager for measuring execution time of code blocks.

    Args:
        name: Optional name for the timer (useful when using multiple timers)
        callback: Optional callback function to process the elapsed time

    Example:
        >>> with TimeIt("data_processing") as timer:
        ...     ...
        ... print(f"Processing took {timer.elapsed:.2f} seconds")
    """

    def __init__(
        self,
        name: Optional[str] = None,
        callback: Optional[Callable[[float], None]] = None,
    ):
        self.name = name or "Timer"
        self.callback = callback
        self.start_time = 0.0
        self.end_time = 0.0
        self._elapsed = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> bool:
        self.end_time = time.perf_counter()
        self._elapsed = self.end_time - self.start_time
        if self.callback:
            self.callback(self._elapsed)
        return False  # Don't suppress exceptions

    @property
    def elapsed(self) -> float:
        """Returns the elapsed time in seconds"""
        return self._elapsed

    @property
    def elapsed_ms(self) -> float:
        """Returns the elapsed time in milliseconds"""
        return self._elapsed * 1000

    def __str__(self) -> str:
        return f"{self.name}: {self.elapsed:.3f} seconds"


def get_dcache(**kwargs):
    global _CACHE

    if _CACHE is None:
        _CACHE = _DCache(**kwargs)

    return _CACHE


class _DCache:
    def __init__(
        self,
        cache_dir: str | None = None,
        ttl: int | None = None,
        enable: bool = True,
        **kwargs,
    ):
        self.cache_dir = cache_dir or CacheConfig.CacheDir
        self.ttl = ttl or CacheConfig.TTL
        self.enabled = enable or bool(CacheConfig.Enabled)
        self.cache = Cache(directory=self.cache_dir, timeout=self.ttl)

    def get_status(self) -> str:
        return f"Cache Status: {self.enabled=}, {self.ttl=}, {self.cache_dir=}".replace("self.", "")

    @staticmethod
    def generate_key(is_cls_method: bool, func: Callable, *args, **kwargs) -> str:
        def make_hashable(val):
            if isinstance(val, (str, int, float, bool, type(None))):
                return val

            if isinstance(val, (dt.date, dt.datetime)):
                return val.isoformat()

            if isinstance(val, (list, tuple)):
                return tuple(make_hashable(v) for v in val)

            if isinstance(val, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in val.items()))
            return str(val)

        sig = signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        bound.apply_defaults()
        items = []
        for name, value in sorted(bound.arguments.items()):
            if is_cls_method and name in ("self", "cls"):
                log.debug(f"Skipping {name} for {func.__qualname__}")
                continue
            items.append((name, make_hashable(value)))

        key_tuple = (f"{func.__qualname__}.{func.__name__}", tuple(items))
        key_str = json.dumps(key_tuple, sort_keys=True, default=str)
        key = hashlib.md5(key_str.encode("utf-8")).hexdigest()
        log.debug(f"Generated key: {key_str} [{key}]")

        return key

    def _is_valid_key(self, key: str):
        return isinstance(key, str) and len(key) == 32

    def get_from_cache(self, key: str) -> Any:
        if not self._is_valid_key(key):
            log.error(f"Caching failed! invalid {key=} generated")
            return None
        return self.cache.get(key, default=None)

    def save_to_cache(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if self._is_valid_key(key):
            return self.cache.set(key, value, expire=ttl or self.ttl)

        log.error(f"Failed to retrieve from cache! invalid {key=} generated")
        return False

    def create(self) -> None:
        self.cache = Cache(self.cache_dir)

    def clear(self) -> None:
        self.cache.clear()


def dcache(is_cls_method: bool = False, ttl: Optional[int] = None):
    def inner(func):
        cache = get_dcache()
        log.info(cache.get_status())

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not cache.enabled or kwargs.pop("_skip_cache", False):
                return func(*args, **kwargs)

            key = cache.generate_key(is_cls_method, func, *args, **kwargs)

            if result := cache.get_from_cache(key):
                log.info(f"CacheHit: {key} {type(result)}")
                return result

            result = func(*args, **kwargs)
            cache.save_to_cache(key, result, ttl)
            return result

        return wrapper

    return inner

def pretty_print(val):
    if isinstance(val, dict):
        print(json.dumps(val, indent=4))
    else:
        pprint.pp(val, indent=4, width=80)


_CACHE: Optional[_DCache] = None
