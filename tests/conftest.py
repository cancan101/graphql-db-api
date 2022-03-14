from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

SWAPI_GRAPHQL_API = "graphql://swapi-graphql.netlify.app/.netlify/functions/index"


@pytest.fixture
def swapi_engine() -> Engine:
    return create_engine(SWAPI_GRAPHQL_API)


@pytest.fixture
def swapi_connection(swapi_engine: Engine) -> Generator[Connection, None, None]:
    with swapi_engine.connect() as connection:
        yield connection
