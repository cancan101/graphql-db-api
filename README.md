# graphql-db-api [![PyPI version](https://badge.fury.io/py/sqlalchemy-graphqlapi.svg)](https://badge.fury.io/py/sqlalchemy-graphqlapi) ![main workflow](https://github.com/cancan101/graphql-db-api/actions/workflows/main.yml/badge.svg) [![codecov](https://codecov.io/gh/cancan101/graphql-db-api/branch/main/graph/badge.svg?token=TOI17GOA2O)](https://codecov.io/gh/cancan101/graphql-db-api)

A Python DB API 2.0 for GraphQL APIs

This module allows you to query GraphQL APIs using SQL.

## SQLAlchemy support

This module provides a SQLAlchemy dialect.

```python
from sqlalchemy.engine import create_engine

engine = create_engine('graphql://host:port/path?is_https=0')
```

### Example Usage

#### Querying Connections

```python
from sqlalchemy import create_engine
from sqlalchemy import text

# We use GraphQL SWAPI (The Star Wars API) c/o Netlify:
engine = create_engine('graphql://swapi-graphql.netlify.app/.netlify/functions/index')

with engine.connect() as connection:
    # Demonstration of requesting nested resource of homeworld
    # and then selecting fields from it
    for row in connection.execute(text("select name, homeworld__name from 'allPeople?include=homeworld'")):
        print(row)
```

#### Querying Lists

```python
from sqlalchemy import create_engine
from sqlalchemy import text

engine = create_engine('graphql://pet-library.moonhighway.com/')

with engine.connect() as connection:
    for row in connection.execute(text("select id, name from 'allPets?is_connection=0'")):
        print(row)
```

## Superset support

In order to use with Superset, install this package and then use the `graphql` protocol in the SQLAlchemy URI like: `graphql://swapi-graphql.netlify.app/.netlify/functions/index`. We install a [`db_engine_spec`](https://github.com/cancan101/graphql-db-api/blob/main/graphqldb/db_engine_specs.py) so Superset should recognize the driver.

## Roadmap

- [x] Non-Connections top level
- [x] Path traversal (basic)
- [ ] Path traversal (basic + nested)
- [ ] Path traversal (list / connection)
- [x] Bearer Tokens in `Authorization` Header
- [ ] Advanced Auth (e.g. with token refresh)
- [ ] Passing Headers (e.g. Auth in other locations)
- [ ] Filtering
- [ ] Sorting
- [x] Relay Pagination
