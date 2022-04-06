from typing import Any, Dict

import requests


def run_query(
    graphql_api: str, *, query: str, bearer_token: str = None
) -> Dict[str, Any]:
    headers: Dict[str, Any] = {}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    resp = requests.post(graphql_api, json={"query": query}, headers=headers)
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
