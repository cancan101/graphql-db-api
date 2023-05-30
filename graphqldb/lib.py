from __future__ import annotations

import urllib.parse
from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, Union

import requests

if TYPE_CHECKING:
    from sqlalchemy.engine.url import URL

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


def run_query(
    graphql_api: str,
    *,
    query: str,
    bearer_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    # TODO(cancan101): figure out timeouts
    resp = requests.post(  # noqa: S113
        graphql_api, json={"query": query}, headers=headers
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as ex:
        # For now let's assume 400 will have errors
        # https://github.com/graphql/graphql-over-http/blob/main/spec/GraphQLOverHTTP.md#status-codes
        if ex.response.status_code != 400:
            raise

    resp_data = resp.json()

    if "errors" in resp_data:
        raise ValueError(resp_data["errors"])

    return resp_data["data"]
