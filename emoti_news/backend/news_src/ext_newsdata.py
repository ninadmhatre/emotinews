import datetime as dt
from functools import lru_cache
from typing import Any, TypeAlias

import httpx

from emoti_news.backend.news_src.base import API
from emoti_news.config.backend import SOURCE_API_KEY
from emoti_news.database.dal import insert_article, create_all_tables
from emoti_news.dtypes import Counties, Categories, Article
from emoti_news.utils import CaptureCallStatus, TimeIt, dcache
from emoti_news.loggers import backend_logger as log

Country = str
Category = str
APIResponse: TypeAlias = dict[Country, dict[Category, list[dict[str, Any]]]]


class NewsDataIOProvider(API):
    api_name = "newsdata.io"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or SOURCE_API_KEY.get(self.api_name)
        self._base_url = "https://newsdata.io/api/1/latest"

        assert self._api_key, "API Key is null, please check..."

        create_all_tables()

    @dcache(is_cls_method=True)
    def _get_top_headlines(self, url: str) -> dict[str, Any]:
        return httpx.get(url).json()  # TODO: Change to async?

    @staticmethod
    @lru_cache()
    def _get_tz(country: str) -> str:
        return {
            "us": "America/New_York",
            "gb": "Europe/London",
            "in": "Asia/Kolkata",
        }[country]

    def _build_url(self, country: str, category: str) -> str:
        tz = self._get_tz(country)

        return (
            f"{self._base_url}?"
            f"apikey={self._api_key}"
            f"&country={country}"
            f"&language=en"
            f"&category={category}"
            f"&timezone={tz}"
            f"&removeduplicate=1"
        )

    def get_headlines(self, countries: list[str], categories: list[str]) -> APIResponse:
        headlines: dict[str, Any] = {}

        for country in countries:
            if country not in headlines:
                headlines[country] = {}
            for category in categories:
                if category not in headlines[country]:
                    headlines[country][category] = []

                log.info(f"fetching {country}.{category}")

                with CaptureCallStatus(country, category) as status:
                    url = self._build_url(country, category)
                    error = None
                    with TimeIt() as tm:
                        top_headlines = self._get_top_headlines(url)

                        if top_headlines["status"] != "success":
                            log.error(f"API returned Not-Ok response for '{country}.{category}'")
                            error = "API retuned 'Not-Ok'"
                            top_headlines = {}
                            rows_fetched = 0
                        else:
                            rows_fetched = len(top_headlines["results"])

                    status.meta.update(
                        {
                            "elapsed_time": tm.elapsed,
                            "error": error,
                            "rows_fetched": rows_fetched,
                        }
                    )

                    log.debug(f"Got {len(top_headlines)} headlines for {country}.{category} [error={error}]")
                    headlines[country][category] = top_headlines

        return headlines

    def parse(self, response: dict, keep_last_n_days: int = 1) -> list[Article]:
        cutoff_date = dt.date.today() - dt.timedelta(days=keep_last_n_days)

        parsed: list[Article] = []

        for country in response:
            for category in response[country]:
                for article in response[country][category]["results"]:
                    published_at_dt = dt.datetime.fromisoformat(article["pubDate"]).date()
                    if published_at_dt < cutoff_date:
                        continue

                    data = {
                        "source": article["source_name"],
                        "url": article["link"],
                        "title": article["title"],
                        "description": article["description"],
                        "content": article["content"],
                        "published_at": article["pubDate"],
                        "uid": article["article_id"],
                    }

                    _article = Article(country, category, self.api_name, **data)

                    if _article in parsed:
                        continue

                    parsed.append(_article)

        return parsed

    def persist(self, articles: list[Article]):
        insert_article(articles)


def entrypoint(countries: list[Country], categories: list[Category], persist: bool = True) -> list[Article]:
    """Main entry point for the API provider"""
    api = NewsDataIOProvider()

    result = api.get_headlines(countries, categories)
    parsed = api.parse(result)

    if persist:
        api.persist(parsed)

    return parsed


if __name__ == "__main__":
    # entrypoint(["IN"], [Categories.Business])
    pass
