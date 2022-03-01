# graphql-db-api
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

## Roadmap
* [ ] Non-Connections top level
* [x] Path traversal (basic)
* [ ] Path traversal (basic + nested)
* [ ] Path traversal (list / connection)
* [ ] Passing Headers (e.g. Auth)
* [ ] Filtering
* [ ] Sorting
* [ ] Pagination
