import functools
from typing import Any, Callable


class ClassProperty(property):
    def __get__(self, cls: Any, owner: type | None = None) -> Any:
        assert self.fget is not None
        return self.fget.__get__(None, owner)()


class multimethod:
    """
    Acts like a classmethod when invoked from the class and like an
    instancemethod when invoked from the instance.
    """

    func: Callable[..., Any]

    def __init__(self, func: Callable[..., Any]):
        self.func = func

    def __get__(self, instance: Any | None, owner: type | None) -> Any:
        """
        If called on an instance, pass the instance as the first
        argument.
        """
        return (
            functools.partial(self.func, owner)
            if instance is None
            else functools.partial(self.func, owner, instance)
        )
