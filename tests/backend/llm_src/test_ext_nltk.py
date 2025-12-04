from emoti_news.dtypes import RawModelRequest, ModelResponse
from emoti_news.backend.llm_src.ext_nltk import LocalNLTK


def test_positive_sentiment():
    l = LocalNLTK()
    data = [
        RawModelRequest(
            uid="pos_1",
            title="I absolutely love this! What a fantastic and uplifting report.",
            description="",
            category="",
            country="",
        )
    ]

    res_raw = l.send(data)
    res_parsed = l.parse_all(res_raw)[0]

    assert isinstance(res_parsed, ModelResponse)
    assert res_parsed.sentiment == "positive"


def test_negative_sentiment():
    l = LocalNLTK()
    data = [
        RawModelRequest(
            uid="neg_1",
            title="This is awful and terrible. I hate it.",
            description="",
            category="",
            country="",
        )
    ]

    res = l.send(data)
    assert isinstance(res, list) and len(res) == 1
    assert res[0]["sentiment"] == "negative"
