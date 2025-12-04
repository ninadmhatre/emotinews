import nltk
from typing import Any

from nltk.sentiment.vader import SentimentIntensityAnalyzer

from emoti_news.dtypes import RawModelRequest, ModelResponse, Sentiment, Clickbait
from .base import API


class LocalNLTK(API):
    """Local NLTK-based sentiment analyzer using VADER.

    send(data) accepts a list of dict-like records (articles) and returns a
    list of dicts containing at minimum: uid, sentiment, sentiment_score.

    Sentiment mapping uses standard VADER thresholds:
      - compound >= 0.05 -> positive
      - compound <= -0.05 -> negative
      - otherwise -> neutral
    """

    api_name = "NLTK"

    def __init__(self, model_name: str = "vader_lexicon"):
        self.model_name = model_name

        # Ensure the vader lexicon is available (download if missing)
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            try:
                nltk.download("vader_lexicon", quiet=True)
            except Exception:
                # If download fails, we'll still attempt to instantiate analyzer
                # which will raise a clearer error later.
                pass

        self.analyzer = SentimentIntensityAnalyzer()

    def send(self, data: list[RawModelRequest]) -> list[dict[str, Any]]:
        """Perform sentiment analysis on each record in `data`.

        Each record is expected to contain textual fields such as `title`,
        `description`, `content` or `desc`. We concatenate available fields
        to get the text to score. Returns a list of dicts with keys:
        - uid: identifier (falls back to url/title when uid missing)
        - sentiment: one of 'positive','neutral','negative'
        - sentiment_score: the VADER compound score (float)
        """
        results: list[dict[str, Any]] = []

        for item in data:
            uid = item.uid

            text = f"{item.title} {item.description or ''}".strip()

            if not text:
                compound = 0.0
            else:
                scores = self.analyzer.polarity_scores(text)
                compound = float(scores.get("compound", 0.0))

            if compound >= 0.05:
                sentiment = Sentiment.Positive
            elif compound <= -0.05:
                sentiment = Sentiment.Negative
            else:
                sentiment = Sentiment.Neutral

            results.append(
                {
                    "uid": uid,
                    "sentiment": sentiment,
                    "sentiment_score": compound,
                }
            )

        return results

    def parse(self, response: dict[str, Any]) -> ModelResponse:
        """Convert a single response dict into a ModelResponse dataclass.

        Expects response to contain at least `uid` and `sentiment_score`.
        The confidence field is derived from absolute sentiment_score.
        Clickbait is left as Unknown by this local analyzer.
        """
        uid = response.get("uid", "")
        sentiment_str = response.get("sentiment", Sentiment.Neutral.value)

        try:
            sentiment = Sentiment(sentiment_str)
        except Exception:
            sentiment = Sentiment.Neutral

        score = float(response.get("sentiment_score", 0.0))

        return ModelResponse(uid=uid, sentiment=sentiment, confidence=abs(score), clickbait=Clickbait.Unknown)

    def parse_batch(self, responses: list[dict[str, Any]]) -> list[ModelResponse]:
        """Convert a list of response dicts into a list of ModelResponse dataclasses."""

        return [self.parse(resp) for resp in responses]

    parse_all = parse_batch
