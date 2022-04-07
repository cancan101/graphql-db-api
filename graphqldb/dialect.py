import urllib.parse
from typing import Any, Dict, List, Sequence, Tuple, Union

from shillelagh.backends.apsw.dialects.base import APSWDialect
from sqlalchemy.engine import Connection
from sqlalchemy.engine.url import URL

from .lib import run_query

# -----------------------------------------------------------------------------

ADAPTER_NAME = "graphql"

# -----------------------------------------------------------------------------


# Imported from: shillelagh.backends.apsw.dialects.gsheets
def extract_query(url: URL) -> Dict[str, Union[str, Sequence[str]]]:
    """
    Extract the query from the SQLAlchemy URL.
    """
    if url.query:
        return dict(url.query)

    # there's a bug in how SQLAlchemy <1.4 handles URLs without hosts,
    # putting the query string as the host; handle that case here
    if url.host and url.host.startswith("?"):
        return dict(urllib.parse.parse_qsl(url.host[1:]))  # pragma: no cover

    return {}


def get_last_query(entry: Union[str, Sequence[str]]) -> str:
    if not isinstance(entry, str):
        entry = entry[-1]
    return entry


# -----------------------------------------------------------------------------


class APSWGraphQLDialect(APSWDialect):
    supports_statement_cache = True

    def __init__(
        self,
        **kwargs: Any,
    ):
        # We tell Shillelagh that this dialect supports just one adapter
        super().__init__(safe=True, adapters=[ADAPTER_NAME], **kwargs)

    def get_table_names(
        self, connection: Connection, schema: str = None, **kwargs: Any
    ) -> List[str]:
        url = connection.engine.url
        graphql_api = self.db_url_to_graphql_api(url)

        query = """{
  __schema {
    queryType {
      fields {
        name
      }
    }
  }
}"""
        bearer_token = str(url.password) if url.password else None
        data = run_query(graphql_api, query=query, bearer_token=bearer_token)

        # TODO(cancan101): filter out "non-Array" returns
        # This is tricky as Connections are non-Array
        return [field["name"] for field in data["__schema"]["queryType"]["fields"]]

    def db_url_to_graphql_api(self, url: URL) -> str:
        query = extract_query(url)
        is_https_param = query.get("is_https", "1")
        is_https = get_last_query(is_https_param) != "0"
        proto = "https" if is_https else "http"
        port_str = "" if url.port is None else f":{url.port}"
        return f"{proto}://{url.host}{port_str}/{url.database}"

    def create_connect_args(
        self,
        url: URL,
    ) -> Tuple[Tuple[()], Dict[str, Any]]:
        args, kwargs = super().create_connect_args(url)

        if "adapter_kwargs" in kwargs and kwargs["adapter_kwargs"] != {}:
            raise ValueError(
                f"Unexpected adapter_kwargs found: {kwargs['adapter_kwargs']}"
            )

        bearer_token = str(url.password) if url.password else None

        query = extract_query(url)
        pagination_relay_param = query.get("is_relay")
        pagination_relay = (
            get_last_query(pagination_relay_param) != "0"
            if pagination_relay_param is not None
            else None
        )

        adapter_kwargs = {
            ADAPTER_NAME: {
                "graphql_api": self.db_url_to_graphql_api(url),
                "bearer_token": bearer_token,
                "pagination_relay": pagination_relay,
            }
        }

        # this seems gross, esp the path override. unclear why memory has to be set here
        return args, {**kwargs, "path": ":memory:", "adapter_kwargs": adapter_kwargs}
