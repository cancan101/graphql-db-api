from typing import Any, Dict

import requests


def run_query(graphql_api: str, *, query: str) -> Dict[str, Any]:
    resp = requests.post(
        graphql_api,
        json={"query": query},
    )
    resp.raise_for_status()
    resp_data = resp.json()

    if "errors" in resp_data:
        raise ValueError(resp_data["errors"])

    return resp_data["data"]
