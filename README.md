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

## Installation
I was having issues getting with `apsw-3.9.2.post1` (the newest version of `apsw` that would install for me from PyPI) and ended up needing to follow [the instructions here](https://shillelagh.readthedocs.io/en/latest/install.html) to build / install from source. There is an [open ticket on the APSW project](https://github.com/rogerbinns/apsw/issues/310) to provide newer wheels.

## Roadmap
* [ ] Non-Connections top level
* [x] Path traversal (basic)
* [ ] Path traversal (basic + nested)
* [ ] Path traversal (list / connection)
* [ ] Passing Headers (e.g. Auth)
* [ ] Filtering
* [ ] Sorting
* [ ] Pagination
