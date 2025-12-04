import datetime as dt
import enum
import hashlib
import json
from enum import StrEnum
from typing import Any, Optional, Callable
import dataclasses as dc


class JobStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SetupAction(StrEnum):
    """Available actions for environment setup"""

    CHECK = "check"
    CREATE = "create"
    RECREATE = "recreate"
    DELETE = "delete"


class Counties(enum.StrEnum):
    US = "us"
    UK = "gb"
    IN = "in"

    @classmethod
    def to_list(cls) -> list[str]:
        return [str(c) for c in cls]


class Categories(enum.StrEnum):
    Business = "business"
    Entertainment = "entertainment"
    General = "general"
    Health = "health"
    Science = "science"
    Sports = "sports"
    Tech = "technology"

    @classmethod
    def to_list(cls) -> list[str]:
        return [str(c) for c in cls]


class Article:
    def __init__(
        self,
        country: str,
        category: str,
        news_api: str,
        source: str,
        url: str,
        title: str,
        description: Optional[str],
        content: Optional[str],
        published_at: str,
        uid: Optional[str] = None,
    ):
        self.country = country
        self.category = category
        self.news_api = news_api
        self.source = source
        self.url = url
        self.title = title
        self.desc = description or ""
        self.content = content or ""
        self.published_at = dt.datetime.fromisoformat(published_at)
        self.uid = uid or self._generate_uid()
        self.sentiment: Optional[str] = None
        self.sentiment_score: Optional[float] = None
        self.is_clickbait: Optional[bool] = None

    def _generate_uid(self) -> str:
        return hashlib.md5(self.url.encode("utf-8")).hexdigest()

    def __eq__(self, other):
        if isinstance(other, Article):
            return self.uid == other.uid
        return False

    def as_dict(self, skip_keys: Optional[list[str]] = None) -> dict[str, str]:
        def if_not_skip(val: Any, key: str) -> Any:
            if skip_keys and key in skip_keys:
                return "<SKIPPED>"
            return val

        data = {
            "uid": if_not_skip(self.uid, "uid"),
            "country": if_not_skip(self.country, "country"),
            "category": if_not_skip(self.category, "category"),
            "source": if_not_skip(self.source, "source"),
            "url": if_not_skip(self.url, "url"),
            "title": if_not_skip(self.title, "title"),
            "description": if_not_skip(self.desc, "description"),
            "content": if_not_skip(self.content, "content"),
            "news_api": if_not_skip(self.news_api, "news_api"),
        }

        return {k: v for k, v in data.items() if v != "<SKIPPED>"}

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), indent=4, default=str)

    def __str__(self):
        return f"Article(uid={self.uid}, source={self.source}, url={self.url})"

    def __repr__(self):
        return self.as_json()


@dc.dataclass(frozen=True)
class JobSpec:
    id: str
    trigger: Any
    job_func: Callable
    job_args: list[Any] = dc.field(default_factory=list)
    job_kwargs: dict[str, Any] = dc.field(default_factory=dict)
    scheduler_kwargs: dict[str, Any] = dc.field(default_factory=dict)

    def as_json(self) -> str:
        return json.dumps(dc.asdict(self), indent=4, default=str)

    def as_dict(self) -> dict[str, Any]:
        return dc.asdict(self)


class Sentiment(StrEnum):
    Neutral = "neutral"
    Positive = "positive"
    Negative = "negative"


class Clickbait(enum.Enum):
    Yes = 1
    No = 0
    Unknown = -1


@dc.dataclass(frozen=True)
class RawModelRequest:
    uid: str
    title: str
    description: Optional[str]
    category: Optional[str]
    country: Optional[str]


class ModelRequest:
    def __init__(self, data: RawModelRequest, prompt: str, model: str, max_tokens: int = 1000):
        self.data = data
        self.prompt = prompt
        self.model = model
        self.max_tokens = max_tokens

    def as_dict(self) -> dict[str, Any]:
        return {
            "data": self.data,
            "prompt": self.prompt,
            "model": self.model,
            "max_tokens": self.max_tokens,
        }


class ModelResponse:
    def __init__(self, uid: str, sentiment: Sentiment, confidence: float, clickbait: Clickbait):
        self.uid = uid
        self.sentiment = sentiment
        self.confidence = confidence
        self.clickbait = clickbait
