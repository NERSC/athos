import pytest

from athos.utils import parse_overrides


def test_parse_overrides_nested_and_yaml():
    result = parse_overrides(
        [
            "models.test_model.temperature=0.1",
            "models.test_model.max_tokens=5",
            "flag=true",
            "items=[1, 2]",
        ]
    )
    assert result == {
        "models": {"test_model": {"temperature": 0.1, "max_tokens": 5}},
        "flag": True,
        "items": [1, 2],
    }


def test_parse_overrides_invalid():
    with pytest.raises(ValueError):
        parse_overrides(["invalidoverride"])
