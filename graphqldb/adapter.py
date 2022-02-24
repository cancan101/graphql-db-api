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
        query_fields = data_tables_and_types["__schema"]["queryType"]["fields"]
        # find the matching query (a field on the query object)
        query_field_type = [x for x in query_fields if x["name"] == table][0]["type"]

        query_field_type_name = query_field_type["name"]

        query_type_info = """query TypeInfo($typeName: String!) {
  __type(name: $typeName) {
    name
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
      }
    }
  }
}"""

        data_type_info = run_query(
            self.graphql_api,
            query=query_type_info,
            variables={"typeName": query_field_type_name},
        )
        data_type_info_type = data_type_info["__type"]

        # we are assuming a top level connection
        edges_info = [x for x in data_type_info_type["fields"] if x["name"] == "edges"][
            0
        ]["type"]["ofType"]
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
