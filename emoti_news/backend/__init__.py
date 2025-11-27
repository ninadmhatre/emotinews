from typing import Callable

from emoti_news.config.backend import NEWS_SOURCE
from emoti_news.dtypes import Article
from .news_src import newsdata_entrypoint, newsapi_entrypoint


def get_entrypoint() -> Callable[[list[str], list[str]], list[Article]]:
    return {"newsapi": newsapi_entrypoint, "newsdata": newsdata_entrypoint}[NEWS_SOURCE]
