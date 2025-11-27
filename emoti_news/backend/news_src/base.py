from typing import Protocol, Any

from emoti_news.dtypes import Article


class API(Protocol):
    api_name: str

    def get_headlines(
        self, countries: list[str], categories: list[str]
    ) -> dict[str, Any]: ...

    def parse(self, response: dict, keep_last_n_days: int = 1) -> list[Article]: ...

    def persist(self, articles: list[Article]): ...
