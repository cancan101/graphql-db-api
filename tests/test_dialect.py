from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine


def test_create_engine(swapi_engine: Engine) -> None:
    pass


def test_get_table_names(swapi_connection: Connection) -> None:
    insp = inspect(swapi_connection)

    tables = insp.get_table_names()

    assert "allPlanets" in tables
    assert "allPeople" in tables
    assert "allSpecies" in tables


def test_query(swapi_connection: Connection) -> None:
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
