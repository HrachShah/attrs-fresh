# SPDX-License-Identifier: MIT

"""
Commonly useful filters for `attrs.asdict` and `attrs.astuple`.
"""

from ._make import Attribute


def _split_what(what):
    """
    Returns a tuple of `frozenset`s of classes and attributes.
    """
    return (
        frozenset(cls for cls in what if isinstance(cls, type)),
        frozenset(cls for cls in what if isinstance(cls, str)),
        frozenset(cls for cls in what if isinstance(cls, Attribute)),
    )


def _matches_type(value, cls):
    """
    Check if *value* is an instance of any class in the type *cls* set.

    The class match uses :func:`isinstance` so subclass instances are picked
    up too -- e.g. an ``include(int)`` filter will include a user-defined
    ``class MyInt(int): ...`` value, not just literal ``int`` instances.
    An empty *cls* set means "no type filter", which falls through to the
    name / attribute branches.
    """
    if not cls:
        return False
    return isinstance(value, tuple(cls))


def include(*what):
    """
    Create a filter that only allows *what*.

    Args:
        what (list[type, str, attrs.Attribute]):
            What to include. Can be a type, a name, or an attribute.

    Returns:
        Callable:
            A callable that can be passed to `attrs.asdict`'s and
            `attrs.astuple`'s *filter* argument.

    .. versionchanged:: 23.1.0 Accept strings with field names.
    .. versionchanged:: 26.2.0 Match type filters with :func:`isinstance`
       instead of exact ``type(value) in cls`` so subclasses are included.
    """
    cls, names, attrs = _split_what(what)

    def include_(attribute, value):
        return (
            _matches_type(value, cls)
            or attribute.name in names
            or attribute in attrs
        )

    return include_


def exclude(*what):
    """
    Create a filter that does **not** allow *what*.

    Args:
        what (list[type, str, attrs.Attribute]):
            What to exclude. Can be a type, a name, or an attribute.

    Returns:
        Callable:
            A callable that can be passed to `attrs.asdict`'s and
            `attrs.astuple`'s *filter* argument.

    .. versionchanged:: 23.3.0 Accept field name string as input argument
    .. versionchanged:: 26.2.0 Match type filters with :func:`isinstance`
       instead of exact ``type(value) in cls`` so subclasses are excluded too.
    """
    cls, names, attrs = _split_what(what)

    def exclude_(attribute, value):
        return not (
            _matches_type(value, cls)
            or attribute.name in names
            or attribute in attrs
        )

    return exclude_
