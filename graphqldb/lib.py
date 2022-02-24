from typing import Any, Dict

import requests


def run_query(
    graphql_api: str, *, query: str, variables: Dict[str, Any] = None
) -> Dict[str, Any]:
    variables = variables or {}
    resp = requests.post(
        graphql_api,
        json={"query": query, "variables": variables},
    )
    resp.raise_for_status()
    resp_data = resp.json()

    if "errors" in resp_data:
        raise ValueError(resp_data["errors"])

    return resp_data["data"]
