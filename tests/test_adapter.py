import pytest

from graphqldb.adapter import extract_flattened_value, get_gql_fields

# -----------------------------------------------------------------------------


def test_get_gql_fields_single():
    assert get_gql_fields(["foo"]) == "foo"


def test_get_gql_fields_multiple():
    assert get_gql_fields(["foo", "bar"]) == "foo bar"


def test_get_gql_fields_nested():
    assert get_gql_fields(["foo", "fooz__bar", "fooz__foo"]) == "foo fooz {bar foo}"


def test_get_gql_fields_nested_grouping():
    assert get_gql_fields(["fooz__bar", "foo", "fooz__foo"]) == "fooz {bar foo} foo"


def test_get_gql_fields_nested_multiple():
    assert (
        get_gql_fields(["fooz__bar", "foo", "barzz__foo"])
        == "fooz {bar} foo barzz {foo}"
    )


def test_extract_flattened_value():
    data = {"foo": 1}
    assert extract_flattened_value(data, "foo") == 1
    assert extract_flattened_value(data, "bar") is None
    assert extract_flattened_value(data, "biz__bar") is None

    with pytest.raises(TypeError):
        assert extract_flattened_value(data, "foo__bar") is None


def test_extract_flattened_value_nested():
    data = {"foo": {"bar": 2}}
    assert extract_flattened_value(data, "foo__bar") == 2
    assert extract_flattened_value(data, "foo__bar2") is None
