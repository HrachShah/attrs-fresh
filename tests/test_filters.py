# SPDX-License-Identifier: MIT

"""
Tests for `attr.filters`.
"""

import pytest

import attr

from attr import fields
from attr.filters import _split_what, exclude, include


@attr.s
class C:
    a = attr.ib()
    b = attr.ib()


class TestSplitWhat:
    """
    Tests for `_split_what`.
    """

    def test_splits(self):
        """
        Splits correctly.
        """
        assert (
            frozenset((int, str)),
            frozenset(("abcd", "123")),
            frozenset((fields(C).a,)),
        ) == _split_what((str, "123", fields(C).a, int, "abcd"))


class TestInclude:
    """
    Tests for `include`.
    """

    @pytest.mark.parametrize(
        ("incl", "value"),
        [
            ((int,), 42),
            ((str,), "hello"),
            ((str, fields(C).a), 42),
            ((str, fields(C).b), "hello"),
            (("a",), 42),
            (("a",), "hello"),
            (("a", str), 42),
            (("a", fields(C).b), "hello"),
        ],
    )
    def test_allow(self, incl, value):
        """
        Return True if a class or attribute is included.
        """
        i = include(*incl)
        assert i(fields(C).a, value) is True

    @pytest.mark.parametrize(
        ("incl", "value"),
        [
            ((str,), 42),
            ((int,), "hello"),
            ((str, fields(C).b), 42),
            ((int, fields(C).b), "hello"),
            (("b",), 42),
            (("b",), "hello"),
            (("b", str), 42),
            (("b", fields(C).b), "hello"),
        ],
    )
    def test_drop_class(self, incl, value):
        """
        Return False on non-included classes and attributes.
        """
        i = include(*incl)
        assert i(fields(C).a, value) is False


class TestExclude:
    """
    Tests for `exclude`.
    """

    @pytest.mark.parametrize(
        ("excl", "value"),
        [
            ((str,), 42),
            ((int,), "hello"),
            ((str, fields(C).b), 42),
            ((int, fields(C).b), "hello"),
            (("b",), 42),
            (("b",), "hello"),
            (("b", str), 42),
            (("b", fields(C).b), "hello"),
        ],
    )
    def test_allow(self, excl, value):
        """
        Return True if class or attribute is not excluded.
        """
        e = exclude(*excl)
        assert e(fields(C).a, value) is True

    @pytest.mark.parametrize(
        ("excl", "value"),
        [
            ((int,), 42),
            ((str,), "hello"),
            ((str, fields(C).a), 42),
            ((str, fields(C).b), "hello"),
            (("a",), 42),
            (("a",), "hello"),
            (("a", str), 42),
            (("a", fields(C).b), "hello"),
        ],
    )
    def test_drop_class(self, excl, value):
        """
        Return True on non-excluded classes and attributes.
        """
        e = exclude(*excl)
        assert e(fields(C).a, value) is False


class MyInt(int):
    """A trivial int subclass used to test that filter type matching is
    based on ``isinstance`` rather than exact ``type()`` equality."""


class TestSubclassMatching:
    """
    A filter that mentions a base class should also match subclasses of it,
    because the user expressed an "is-a" intent by passing the type. A
    value of type ``int`` matches ``include(int)`` and a value of type
    ``MyInt(int)`` should also match it -- otherwise ``include(int)``
    silently drops subclass instances, which is surprising and undocumented.
    """

    def test_include_matches_subclass(self):
        """
        ``include(BaseCls)`` returns True for a value of a subclass of
        ``BaseCls`` (the original code only matched exact ``type(value)``).
        """
        i = include(int)
        assert i(fields(C).a, 42) is True  # exact int
        assert i(fields(C).a, MyInt(42)) is True  # subclass of int

    def test_exclude_drops_subclass(self):
        """
        ``exclude(BaseCls)`` returns False for a value of a subclass of
        ``BaseCls``.
        """
        e = exclude(int)
        assert e(fields(C).a, 42) is False  # exact int
        assert e(fields(C).a, MyInt(42)) is False  # subclass of int

    def test_include_subclass_not_included_without_match(self):
        """
        ``include(SubCls)`` does not match a value whose type is the base
        class but not the subclass (the type filter is one-way: subclasses
        match, supertypes do not).
        """
        i = include(MyInt)
        assert i(fields(C).a, MyInt(42)) is True
        assert i(fields(C).a, 42) is False

    def test_include_empty_class_set_falls_through(self):
        """
        An empty class set must not raise; it just contributes nothing to
        the OR chain so the rest of the predicate decides.
        """
        i = include("a")  # only name-based, no class
        assert i(fields(C).a, 42) is True  # name match
        assert i(fields(C).b, 42) is False  # name mismatch, no class

    def test_exclude_empty_class_set_falls_through(self):
        """
        ``exclude()`` with no class arg still allows every value through
        (name and Attribute matching is the only way to exclude).
        """
        e = exclude("a")
        assert e(fields(C).a, 42) is False
        assert e(fields(C).b, 42) is True
