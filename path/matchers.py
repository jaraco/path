from __future__ import annotations

import fnmatch
import ntpath
import types
from typing import TYPE_CHECKING, Any, Callable, overload

if TYPE_CHECKING:
    from typing_extensions import Literal


def _same_normalizer(left: Callable, right: Callable) -> bool:
    """Compare callable normalizers without invoking custom equality."""
    if left is right:
        return True

    if isinstance(left, types.MethodType) and isinstance(right, types.MethodType):
        return left.__self__ is right.__self__ and left.__func__ is right.__func__

    if isinstance(left, types.BuiltinMethodType) and isinstance(
        right, types.BuiltinMethodType
    ):
        # Built-in bound methods lack __func__, but their method objects are
        # recreated on access and share their owner and method name.
        owner = left.__self__
        return (
            owner is not None
            and not isinstance(owner, types.ModuleType)
            and owner is right.__self__
            and left.__name__ == right.__name__
        )

    return False


class _PatternCache:
    """Transient cache state; omit callables when a Pattern is pickled."""

    def __init__(self) -> None:
        self._entry: tuple[Callable[[str], str], str] | None = None

    def __reduce__(self) -> Any:
        # Pattern's regular dict/slot state remains intact, while a possibly
        # unpicklable normalizer is discarded and recomputed after loading.
        return (type(self), ())

    def get_pattern(self, pattern: str, normcase: Callable[[str], str]) -> str:
        entry = self._entry
        if entry is not None:
            cached_normalizer, cached_pattern = entry
            if _same_normalizer(cached_normalizer, normcase):
                return cached_pattern

        normalized = normcase(pattern)
        self._entry = (normcase, normalized)
        return normalized


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
    _pattern_cache: _PatternCache

    def __init__(self, pattern: str):
        self.pattern = pattern

    def get_pattern(self, normcase: Callable[[str], str]) -> str:
        try:
            cache = self._pattern_cache
        except AttributeError:
            # Lazily initialize so older pickles without the cache remain valid.
            cache = self._pattern_cache = _PatternCache()
        return cache.get_pattern(self.pattern, normcase)

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
