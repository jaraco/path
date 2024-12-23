from __future__ import annotations

import functools
from typing import Any, Callable, Generic, TypeVar


class ClassProperty(property):
    def __get__(self, cls: Any, owner: type | None = None) -> Any:
        assert self.fget is not None
        return self.fget.__get__(None, owner)()


_T = TypeVar("_T")


class multimethod(Generic[_T]):
    """
    Acts like a classmethod when invoked from the class and like an
    instancemethod when invoked from the instance.
    """

    func: Callable[..., _T]

    def __init__(self, func: Callable[..., _T]):
        self.func = func

    def __get__(self, instance: _T | None, owner: type[_T] | None) -> Callable[..., _T]:
        """
        If called on an instance, pass the instance as the first
        argument.
        """
        return (
            functools.partial(self.func, owner)
            if instance is None
            else functools.partial(self.func, owner, instance)
        )
