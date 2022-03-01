import sys
from collections import defaultdict
from typing import Any, Collection, Dict, Iterator, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from shillelagh.adapters.base import Adapter
from shillelagh.fields import Boolean, Field, Filter, Float, Integer, String
from shillelagh.typing import RequestedOrder

from .lib import run_query

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


def parse_gql_type(type_info: TypeInfo) -> Optional[Field]:
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
    new_path = path + [field_obj["name"]]

    kind = field_obj["type"]["kind"]
    if kind == "SCALAR":
        field_field = parse_gql_type(field_obj["type"])
        return {"__".join(new_path): field_field}
    elif kind == "NON_NULL":
        of_type = field_obj["type"]["ofType"]

        if of_type is None:
            raise ValueError("of_type is None")

        of_type_name = of_type["name"]
        if of_type_name is None:
            raise ValueError("of_type_name is None")

        return get_type_entries(
            FieldInfo(
                name=field_obj["name"],
                type=data_types[of_type_name],
            ),
            data_types=data_types,
            include=include,
            path=path,
        )
    else:
        # TODO(cancan101): other types to handle:
        # LIST, ENUM, UNION, INTERFACE, OBJECT (implicitly handled)
        if field_obj["name"] in include:
            ret = {}
            name = field_obj["type"]["name"]
            if name is None:
                return {}
            fields = data_types[name]["fields"] or []
            for field in fields:
                ret.update(
                    get_type_entries(
                        field, data_types=data_types, include=include, path=new_path
                    )
                )
            return ret

        return {}


# clean these up:
def find_by_name(name: str, *, types: List[FieldInfo]) -> FieldInfo:
    return [x for x in types if x["name"] == name][0]


def find_type_by_name(name: str, *, types: List[FieldInfo]) -> TypeInfo:
    return find_by_name(name, types=types)["type"]


class GraphQLAdapter(Adapter):
    safe = True

    def __init__(
        self,
        table: str,
        include: Collection[str],
        graphql_api: str,
    ):
        super().__init__()

        self.table = table
        self.include = set(include)

        self.graphql_api = graphql_api

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

        query_type_and_types = run_query(
            self.graphql_api, query=query_type_and_types_query
        )
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

        def get_type_fields(name: str) -> List[FieldInfo]:
            return data_types[name]["fields"] or []

        query_return_fields = get_type_fields(query_return_type_name)

        def get_edges_type_name(fields: List[FieldInfo]) -> Optional[str]:
            edges_info = find_type_by_name("edges", types=fields)["ofType"]
            if edges_info is None:
                return None
            return edges_info["name"]

        def get_node_type_name(fields: List[FieldInfo]) -> Optional[str]:
            node_info = find_type_by_name("node", types=fields)
            return node_info["name"]

        # we are assuming a top level connection
        edges_type_name = get_edges_type_name(query_return_fields)
        if edges_type_name is None:
            raise ValueError("Unable to resolve edges_type_name")

        edges_fields = get_type_fields(edges_type_name)

        node_type_name = get_node_type_name(edges_fields)
        if node_type_name is None:
            raise ValueError("Unable to resolve node_type_name")

        node_fields = get_type_fields(node_type_name)

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
        include: List[str]
        if include_entry:
            include = []
            for i in include_entry:
                include.extend(i.split(","))
        else:
            include = []

        return (parsed.path, include)

    def get_columns(self) -> Dict[str, Field]:
        return self.columns

    def get_data(
        self,
        bounds: Dict[str, Filter],
        order: List[Tuple[str, RequestedOrder]],
    ) -> Iterator[Dict[str, Any]]:

        # TODO(cancan101): actually nest this
        def get_field_str(fields: List[str], root: str = None) -> str:
            ret = " ".join(fields)
            if root is not None:
                ret = f"{root} {{{ret}}}"
            return ret

        mappings: Dict[Optional[str], List[str]] = defaultdict(list)
        for field in [x.split("__", 1) for x in self.columns.keys()]:
            if len(field) == 1:
                mappings[None].append(field[-1])
            else:
                mappings[field[0]].append(field[-1])
        fields_str = " ".join(
            get_field_str(fields, root=root) for root, fields in mappings.items()
        )

        query = f"""query {{
  {self.table}{{
    edges{{
      node{{
        {fields_str}
      }}
    }}
  }}
}}"""
        query_data = run_query(self.graphql_api, query=query)

        def getter(node: Dict[str, Any], field_name: str) -> Any:
            ret: Any = node
            for path in field_name.split("__"):
                if ret is None:
                    return ret
                ret = ret.get(path)
            return ret

        for edge in query_data[self.table]["edges"]:
            node: Dict[str, Any] = edge["node"]

            yield {c: getter(node, c) for c in self.columns.keys()}
