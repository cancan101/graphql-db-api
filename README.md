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
* [ ] Non-connections top level
* [ ] Path traversal
* [ ] Filtering
* [ ] Sorting
* [ ] Pagination
