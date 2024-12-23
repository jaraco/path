from __future__ import annotations

import fnmatch
import ntpath
from typing import TYPE_CHECKING, Any, Callable, overload

if TYPE_CHECKING:
    from typing_extensions import Literal


@overload
def load(param: None) -> Null: ...


@overload
def load(param: str) -> Pattern: ...


@overload
def load(param: Any) -> Any: ...


def load(param):
    """
    If the supplied parameter is a string, assume it's a simple
    pattern.
    """
    return (
        Pattern(param)
        if isinstance(param, str)
        else param
        if param is not None
        else Null()
    )


class Base:
    pass


class Null(Base):
    def __call__(self, path: str) -> Literal[True]:
        return True


class Pattern(Base):
    pattern: str
    _pattern: str

    def __init__(self, pattern: str):
        self.pattern = pattern

    def get_pattern(self, normcase: Callable[[str], str]) -> str:
        try:
            return self._pattern
        except AttributeError:
            pass
        self._pattern = normcase(self.pattern)
        return self._pattern

    # NOTE: 'path' should be annotated with Path, but cannot due to circular imports.
    def __call__(self, path) -> bool:
        normcase = getattr(self, 'normcase', path.module.normcase)
        pattern = self.get_pattern(normcase)
        return fnmatch.fnmatchcase(normcase(path.name), pattern)


class CaseInsensitive(Pattern):
    """
    A Pattern with a ``'normcase'`` property, suitable for passing to
    :meth:`iterdir`, :meth:`dirs`, :meth:`files`, :meth:`walk`,
    :meth:`walkdirs`, or :meth:`walkfiles` to match case-insensitive.

    For example, to get all files ending in .py, .Py, .pY, or .PY in the
    current directory::

        from path import Path, matchers
        Path('.').files(matchers.CaseInsensitive('*.py'))
    """

    normcase = staticmethod(ntpath.normcase)
