from typing import Protocol

from emoti_news.dtypes import RawModelRequest, ModelResponse

class API(Protocol):
    model_name: str

    def send(self, data: list[RawModelRequest]) -> list[dict[str, str]]: ...

    def parse(self, response: dict) -> ModelResponse: ...