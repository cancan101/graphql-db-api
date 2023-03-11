from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine, make_url

from graphqldb.dialect import APSWGraphQLDialect


def test_create_engine(swapi_engine: Engine) -> None:
    pass


def test_get_table_names_connections(swapi_connection: Connection) -> None:
    insp = inspect(swapi_connection)

    tables = insp.get_table_names()

    # TODO(cancan101): This should also test for tables shouldn't be here
    assert "allPlanets" in tables
    assert "allPeople" in tables
    assert "allSpecies" in tables


def test_get_table_names_lists(petstore_connection: Connection) -> None:
    insp = inspect(petstore_connection)

    tables = insp.get_table_names()

    # TODO(cancan101): This should also test for tables shouldn't be here
    assert "allPets" in tables
    assert "allCustomers" in tables


def test_query_connection(swapi_connection: Connection) -> None:
    result = swapi_connection.execute(
        text(
            """select
                name,
                height,
                mass,
                homeworld__name
            from
                'allPeople?include=homeworld'"""
        )
    )
    assert len(list(result)) == 82


def test_query_paginate(swapi_connection: Connection) -> None:
    result = swapi_connection.execute(
        text(
            """select
                id
            from
                'allPeople?arg_after=YXJyYXljb25uZWN0aW9uOjA=&iarg_first=50'"""
        )
    )
    assert len(list(result)) == 81


def test_query_no_paginate(swapi_connection_no_relay: Connection) -> None:
    result = swapi_connection_no_relay.execute(
        text(
            """select
                id
            from
                'allPeople?iarg_first=3'"""
        )
    )
    assert len(list(result)) == 3


def test_query_no_paginate_XXXX(petstore_connection: Connection) -> None:
    result = petstore_connection.execute(
        text(
            """select
                id
            from
                'allPets?is_connection=0'"""
        )
    )
    assert len(list(result)) == 25


def test_db_url_to_graphql_api():
    url_http = make_url("graphql://host:123/path?is_https=0")
    assert (
        APSWGraphQLDialect().db_url_to_graphql_api(url_http) == "http://host:123/path"
    )

    url_https = make_url("graphql://host:123/path?is_https=1")
    assert (
        APSWGraphQLDialect().db_url_to_graphql_api(url_https) == "https://host:123/path"
    )
