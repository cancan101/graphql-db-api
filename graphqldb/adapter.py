from typing import Any, Dict, Iterator, List, Optional, Tuple

from shillelagh.adapters.base import Adapter
from shillelagh.fields import Boolean, Field, Filter, Float, Integer, String
from shillelagh.typing import RequestedOrder

from .lib import run_query

# -----------------------------------------------------------------------------


def parse_gql_type(type_obj) -> Optional[Field]:
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


def get_type_entries(field_obj) -> Dict[str, Field]:
    field_field = parse_gql_type(field_obj["type"])
    if field_field is None:
        # array
        return {}
    else:
        return {field_obj["name"]: field_field}


def find_by_name(name: str, *, types: list) -> dict:
    return [x for x in types if x["name"] == name][0]


def find_type_by_name(name: str, *, types: list) -> dict:
    return find_by_name(name, types=types)["type"]


class GraphQLAdapter(Adapter):
    safe = True

    def __init__(
        self,
        table: str,
        graphql_api: str,
    ):
        super().__init__()

        self.table = table

        self.graphql_api = graphql_api

        query_tables_and_types = """{
  __schema {
    queryType {
      fields {
        name
        type {
          name
        }
      }
    }
  }
}"""

        data_tables_and_types = run_query(
            self.graphql_api, query=query_tables_and_types
        )
        query_return_fields = data_tables_and_types["__schema"]["queryType"]["fields"]

        # find the matching query (a field on the query object)
        query_field_type = find_type_by_name(table, types=query_return_fields)
        query_return_type_name = query_field_type["name"]

        query_types_info = """{
  __schema {
    types {
      name
      fields {
        name
        type {
          name
          ofType {
            name
          }
        }
      }
    }
  }
}"""

        data_types_info = run_query(
            self.graphql_api,
            query=query_types_info,
        )
        data_types = data_types_info["__schema"]["types"]

        def get_type_fields(name: str):
            return find_by_name(name, types=data_types)["fields"]

        query_return_fields = get_type_fields(query_return_type_name)

        def get_edges_type_name(fields) -> str:
            edges_info = find_type_by_name("edges", types=fields)["ofType"]
            return edges_info["name"]

        def get_node_type_name(fields) -> str:
            node_info = find_type_by_name("node", types=fields)
            return node_info["name"]

        # we are assuming a top level connection
        edges_type_name = get_edges_type_name(query_return_fields)
        edges_fields = get_type_fields(edges_type_name)

        node_type_name = get_node_type_name(edges_fields)
        node_fields = get_type_fields(node_type_name)

        self.columns: Dict[str, Field] = {}
        for node_field in node_fields:
            self.columns.update(get_type_entries(node_field))

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
        query = f"""query {{
  {self.table}{{
    edges{{
      node{{
        {" ".join(self.columns.keys())}
      }}
    }}
  }}
}}"""
        query_data = run_query(self.graphql_api, query=query)

        for edge in query_data[self.table]["edges"]:
            node = edge["node"]

            yield {c: node.get(c) for c in self.columns.keys()}
