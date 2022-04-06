from collections import defaultdict
from typing import Any, Collection, Dict, Iterator, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse

from shillelagh.adapters.base import Adapter
from shillelagh.fields import Boolean, Field, Filter, Float, Integer, String
from shillelagh.typing import RequestedOrder

from .lib import run_query
from .types import TypedDict

# -----------------------------------------------------------------------------


class MaybeNamed(TypedDict):
    name: Optional[str]


class TypeInfo(MaybeNamed):
    ofType: Optional[MaybeNamed]
    # technically an enum:
    kind: str


class FieldInfo(TypedDict):
    name: str
    type: TypeInfo


class TypeInfoWithFields(TypeInfo):
    fields: Optional[List[FieldInfo]]


# -----------------------------------------------------------------------------


def parse_gql_type(type_info: TypeInfo) -> Field:
    # TODO(cancan101): do we want to handle Nones here?
    name: Optional[str] = type_info["name"]
    if name == "String":
        return String()
    elif name == "ID":
        # TODO(cancan101): figure out if we want to map this to UUID, etc
        return String()
    elif name == "Int":
        return Integer()
    elif name == "Float":
        return Float()
    elif name == "Boolean":
        return Boolean()
    else:
        # TODO(cancan101): how do we want to handle other scalars?
        raise ValueError(f"Unknown type: {name}")


def get_type_entries(
    field_obj: FieldInfo,
    *,
    data_types: Dict[str, TypeInfoWithFields],
    include: Collection[str],
    path: List[str] = None,
) -> Dict[str, Field]:
    path = path or []

    field_name = field_obj["name"]
    new_path = path + [field_name]

    field_obj_type = field_obj["type"]

    kind = field_obj_type["kind"]
    if kind == "SCALAR":
        field_field = parse_gql_type(field_obj_type)
        return {"__".join(new_path): field_field}
    elif kind == "NON_NULL":
        of_type = field_obj_type["ofType"]

        if of_type is None:
            raise ValueError("of_type is None")

        of_type_name = of_type["name"]
        if of_type_name is None:
            raise ValueError("of_type_name is None")

        return get_type_entries(
            FieldInfo(
                name=field_name,
                type=data_types[of_type_name],
            ),
            data_types=data_types,
            include=include,
            path=path,
        )
    # TODO(cancan101): other types to handle:
    # LIST, ENUM, UNION, INTERFACE, OBJECT (implicitly handled)
    else:
        # Check to see if this is a requested include
        if field_name in include:
            ret = {}
            name = field_obj_type["name"]
            if name is None:
                raise ValueError(f"Unable to get type of: {field_name}")

            fields = data_types[name]["fields"]
            if fields is None:
                raise ValueError(f"Unable to get fields for: {name}")

            for field in fields:
                ret.update(
                    get_type_entries(
                        field, data_types=data_types, include=include, path=new_path
                    )
                )
            return ret

        return {}


# -----------------------------------------------------------------------------


# clean these up:
def find_by_name(name: str, *, types: List[FieldInfo]) -> FieldInfo:
    return [x for x in types if x["name"] == name][0]


def find_type_by_name(name: str, *, types: List[FieldInfo]) -> TypeInfo:
    return find_by_name(name, types=types)["type"]


def get_edges_type_name(fields: List[FieldInfo]) -> Optional[str]:
    edges_info = find_type_by_name("edges", types=fields)["ofType"]
    if edges_info is None:
        return None
    return edges_info["name"]


def get_node_type_name(fields: List[FieldInfo]) -> Optional[str]:
    node_info = find_type_by_name("node", types=fields)
    return node_info["name"]


# -----------------------------------------------------------------------------


def extract_flattened_value(node: Dict[str, Any], field_name: str) -> Any:
    ret: Any = node
    for path in field_name.split("__"):
        if ret is None:
            return ret
        elif not isinstance(ret, dict):
            raise TypeError(f"{field_name} is not dict path")
        ret = ret.get(path)
    return ret


def get_gql_fields(column_names: Sequence[str]) -> str:
    # TODO(cancan101): actually nest this
    def get_field_str(fields: List[str], root: str = None) -> str:
        ret = " ".join(fields)
        if root is not None:
            ret = f"{root} {{{ret}}}"
        return ret

    mappings: Dict[Optional[str], List[str]] = defaultdict(list)
    for field in [x.split("__", 1) for x in column_names]:
        if len(field) == 1:
            mappings[None].append(field[-1])
        else:
            mappings[field[0]].append(field[-1])

    fields_str = " ".join(
        get_field_str(fields, root=root) for root, fields in mappings.items()
    )
    return fields_str


# -----------------------------------------------------------------------------


class GraphQLAdapter(Adapter):
    safe = True

    def __init__(
        self,
        table: str,
        include: Collection[str],
        graphql_api: str,
        bearer_token: str = None,
    ):
        super().__init__()

        self.table = table
        self.include = set(include)

        self.graphql_api = graphql_api
        self.bearer_token = bearer_token

        query_type_and_types_query = """{
  __schema {
    queryType {
      fields {
        name
        type {
          name
        }
      }
    }
    types {
      name
      kind
      fields {
        name
        type {
          name
          kind
          ofType {
            name
          }
        }
      }
    }
  }
}"""

        query_type_and_types = self.run_query(query=query_type_and_types_query)
        query_type_and_types_schema = query_type_and_types["__schema"]
        queries_return_fields: List[FieldInfo] = query_type_and_types_schema[
            "queryType"
        ]["fields"]

        # find the matching query (a field on the query object)
        # TODO(cancan101): handle missing
        query_return_type_name = find_type_by_name(
            self.table, types=queries_return_fields
        )["name"]
        if query_return_type_name is None:
            raise ValueError("Unable to resolve query_return_type_name")

        data_types_list: List[TypeInfoWithFields] = query_type_and_types_schema["types"]
        data_types: Dict[str, TypeInfoWithFields] = {
            t["name"]: t for t in data_types_list if t["name"] is not None
        }

        query_return_fields = data_types[query_return_type_name]["fields"]
        if query_return_fields is None:
            raise ValueError("No fields found on query")

        # we are assuming a top level connection
        edges_type_name = get_edges_type_name(query_return_fields)
        if edges_type_name is None:
            raise ValueError("Unable to resolve edges_type_name")

        edges_fields = data_types[edges_type_name]["fields"]
        if edges_fields is None:
            raise ValueError("No fields found on edge")

        node_type_name = get_node_type_name(edges_fields)
        if node_type_name is None:
            raise ValueError("Unable to resolve node_type_name")

        node_fields = data_types[node_type_name]["fields"]
        if node_fields is None:
            raise ValueError("No fields found on node")

        self.columns: Dict[str, Field] = {}
        for node_field in node_fields:
            self.columns.update(
                get_type_entries(
                    node_field, data_types=data_types, include=self.include
                )
            )

    @staticmethod
    def supports(uri: str, fast: bool = True, **kwargs: Any) -> Optional[bool]:
        # TODO the slow path here could connect to the GQL Server
        return True

    @staticmethod
    def parse_uri(table: str) -> Tuple[str, List[str]]:
        parsed = urlparse(table)
        query_string = parse_qs(parsed.query)

        include_entry = query_string.get("include")
        include: List[str] = []
        if include_entry:
            for i in include_entry:
                include.extend(i.split(","))

        return (parsed.path, include)

    def get_columns(self) -> Dict[str, Field]:
        return self.columns

    def run_query(self, query: str) -> Dict[str, Any]:
        return run_query(self.graphql_api, query=query, bearer_token=self.bearer_token)

    def get_data(
        self,
        bounds: Dict[str, Filter],
        order: List[Tuple[str, RequestedOrder]],
    ) -> Iterator[Dict[str, Any]]:
        fields_str = get_gql_fields(list(self.columns.keys()))

        query = f"""query {{
  {self.table}{{
    edges{{
      node{{
        {fields_str}
      }}
    }}
  }}
}}"""
        query_data = self.run_query(query=query)

        for edge in query_data[self.table]["edges"]:
            node: Dict[str, Any] = edge["node"]

            yield {c: extract_flattened_value(node, c) for c in self.columns.keys()}
