import pytest

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
