from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

SWAPI_GRAPHQL_DB_URL = "graphql://swapi-graphql.netlify.app/.netlify/functions/index"


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
