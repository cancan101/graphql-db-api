import pytest
import responses

from graphqldb.lib import run_query

SWAPI_API = "https://swapi-graphql.netlify.app/.netlify/functions/index"


def test_run_query_error() -> None:
    with pytest.raises(ValueError):
        run_query(
            SWAPI_API,
            query="""{
    allPeople {
        a
    }
    }""",
        )


def test_run_query_bearer_token(mocked_responses: responses.RequestsMock):
    mocked_responses.add(method=responses.POST, url=SWAPI_API, json={"data": {}})
    run_query(SWAPI_API, query="{}", bearer_token="asdf")  # noqa: S106
    assert mocked_responses.calls[0].request.headers["Authorization"] == "Bearer asdf"
