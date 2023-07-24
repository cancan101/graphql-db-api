from typing import Final, Generator

import pytest
import responses
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

# -----------------------------------------------------------------------------

SWAPI_GRAPHQL_DB_URL: Final[
    str
] = "graphql://swapi-graphql.netlify.app/.netlify/functions/index"
PETSTORE_GRAPHQL_DB_URL: Final[str] = "graphql://pet-library.moonhighway.com/"

# -----------------------------------------------------------------------------


@pytest.fixture
def swapi_graphq_db_url() -> str:
    return SWAPI_GRAPHQL_DB_URL


@pytest.fixture
def swapi_engine(swapi_graphq_db_url: str) -> Engine:
    return create_engine(swapi_graphq_db_url)


@pytest.fixture
def swapi_connection(swapi_engine: Engine) -> Generator[Connection, None, None]:
    with swapi_engine.connect() as connection:
        yield connection


@pytest.fixture
def swapi_connection_no_relay(
    swapi_graphq_db_url: str,
) -> Generator[Connection, None, None]:
    swapi_engine_no_relay = create_engine(f"{swapi_graphq_db_url}?is_relay=0")
    with swapi_engine_no_relay.connect() as connection:
        yield connection


@pytest.fixture
def petstore_connection(swapi_engine: Engine) -> Generator[Connection, None, None]:
    petstore_engine = create_engine(PETSTORE_GRAPHQL_DB_URL)
    with petstore_engine.connect() as connection:
        yield connection


@pytest.fixture
def petstore_connection_on_engine(
    swapi_engine: Engine,
) -> Generator[Connection, None, None]:
    petstore_engine = create_engine(PETSTORE_GRAPHQL_DB_URL, list_queries=["allPets"])
    with petstore_engine.connect() as connection:
        yield connection


# -----------------------------------------------------------------------------


@pytest.fixture
def mocked_responses() -> Generator[responses.RequestsMock, None, None]:
    with responses.RequestsMock() as rsps:
        yield rsps
