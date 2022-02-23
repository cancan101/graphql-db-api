from typing import Any, Dict, Iterator, List, Optional, Tuple

import requests
from shillelagh.adapters.base import Adapter
from shillelagh.fields import Boolean, Field, Filter, Float, Integer, String
from shillelagh.typing import RequestedOrder

# -----------------------------------------------------------------------------


def parse_gql_type(type_obj):
    name: Optional[str] = type_obj["name"]
    if name is None:
        # array
        return None
    elif name == "String":
        return String()
    elif name == "Int":
        return Integer()
    elif name == "Float":
        return Float()
    elif name == "Boolean":
        return Boolean()
    elif name.endswith("Connection"):
        # hack
        return None
    else:
        raise ValueError(f"Unknown type: {name}")


def get_type_entries(field_obj):
    field_field = parse_gql_type(field_obj["type"])
    if field_field is None:
        # array
        return {}
    else:
        return {field_obj["name"]: field_field}


class GraphQLAdapter(Adapter):
    safe = True

    def get_url(self):
        proto = "https" if self.is_https else "http"
        port_str = "" if self.port is None else f":{self.port}"
        return f"{proto}://{self.host}{port_str}/{self.path}"

    def __init__(
        self,
        table: str,
        host: str,
        port: str = None,
        path: str = None,
        is_https: bool = True,
    ):
        super().__init__()

        self.table = table

        self.is_https = is_https
        self.host = host
        self.port = port
        self.path = path

        # we can get top level and then just pull in the needed types
        resp = requests.post(
            self.get_url(),
            json={
                "query": """
{
  __schema {
    queryType {
      fields {
        name
        type {
          fields {
            name
            type {
              ofType {
                name
                fields {
                  name
                  type {
                    fields {
                      name
                      type {
                        name
                      }
                    }
                  }
                }
              }
              kind
            }
          }
          name
        }
      }
    }
  }
}
        """
            },
        )
        schema_info = resp.json()
        query_fields = schema_info["data"]["__schema"]["queryType"]["fields"]
        # find the matching query (a field on the quey object)
        table_info = [x for x in query_fields if x["name"] == table][0]["type"]
        # we are assuming a top level connection
        edges_info = [x for x in table_info["fields"] if x["name"] == "edges"][0][
            "type"
        ]["ofType"]
        node_info = [x for x in edges_info["fields"] if x["name"] == "node"][0]

        column_info = node_info["type"]["fields"]

        self.columns: Dict[str, Field] = {}
        for field in column_info:
            self.columns.update(get_type_entries(field))

    @staticmethod
    def supports(uri: str, fast: bool = True, **kwargs: Any) -> Optional[bool]:
        # TODO the slow path here could connect to the GQL Server
        return True

    @staticmethod
    def parse_uri(table: str) -> Tuple[str]:
        return (table,)

    def get_columns(self) -> Dict[str, Field]:
        return self.columns

    def get_data(
        self,
        bounds: Dict[str, Filter],
        order: List[Tuple[str, RequestedOrder]],
    ) -> Iterator[Dict[str, Any]]:

        resp = requests.post(
            self.get_url(),
            json={
                "query": f"""
query{{
  {self.table}{{
    edges{{
      node{{
        {" ".join(self.columns.keys())}
      }}
    }}
  }}
}}
        """
            },
        )
        data = resp.json()
        for edge in data["data"][self.table]["edges"]:
            node = edge["node"]

            yield {c: node.get(c) for c in self.columns.keys()}
