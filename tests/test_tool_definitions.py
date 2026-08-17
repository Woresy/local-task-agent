"""function schema 测试。"""

from app.tools.definitions import TOOL_DEFINITIONS


EXPECTED_TOOL_NAMES = {
    "lookup_metric",
    "query_status",
    "create_summary",
}


def test_three_tool_definitions_exist() -> None:
    assert len(TOOL_DEFINITIONS) == 3


def test_tool_definition_names_are_unique() -> None:
    names = [
        definition["function"]["name"]
        for definition in TOOL_DEFINITIONS
    ]

    assert set(names) == EXPECTED_TOOL_NAMES
    assert len(names) == len(set(names))


def test_every_definition_is_a_function() -> None:
    for definition in TOOL_DEFINITIONS:
        assert definition["type"] == "function"


def test_every_schema_rejects_extra_parameters() -> None:
    for definition in TOOL_DEFINITIONS:
        parameters = definition["function"]["parameters"]

        assert parameters["type"] == "object"
        assert parameters["additionalProperties"] is False


def test_every_property_is_required() -> None:
    for definition in TOOL_DEFINITIONS:
        parameters = definition["function"]["parameters"]

        assert set(parameters["properties"]) == set(
            parameters["required"]
        )


def test_deepseek_normal_endpoint_uses_non_strict_mode() -> None:
    for definition in TOOL_DEFINITIONS:
        assert definition["function"]["strict"] is False