# graphql-db-api
A Python DB API 2.0 for GraphQL APIs

This module allows you to query GraphQL APIs using SQL.

## SQLAlchemy support
This module provides a SQLAlchemy dialect.

```python
from sqlalchemy.engine import create_engine

engine = create_engine('graphql://host:port/path?is_https=0')
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
