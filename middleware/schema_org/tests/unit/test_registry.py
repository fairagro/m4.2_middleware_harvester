"""Unit tests for the reusable Schema.org registry implementation."""

import pytest

from middleware.schema_org.registry import Registry


def test_registry_register_and_getitem() -> None:
    registry = Registry[str, object]()

    @registry.register("foo")
    class ImplB:
        pass

    assert registry["foo"] is ImplB
    assert "foo" in registry


def test_registry_setitem_items_and_keyerror() -> None:
    registry = Registry[str, object]()

    class Impl2:
        pass

    registry["bar"] = Impl2
    assert registry["bar"] is Impl2
    assert list(registry.items()) == [("bar", Impl2)]

    with pytest.raises(KeyError):
        _ = registry["missing"]
