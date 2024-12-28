"""
Path Pie

Implements ``path.Path`` - An object representing a
path to a file or directory.

Example::

    from path import Path
    d = Path('/home/guido/bin')

    # Globbing
    for f in d.files('*.py'):
        f.chmod(0o755)

    # Changing the working directory:
    with Path("somewhere"):
        # cwd in now `somewhere`
        ...

    # Concatenate paths with /
    foo_txt = Path("bar") / "foo.txt"
"""

from __future__ import annotations

import builtins
import contextlib
import datetime
import errno
import fnmatch
import functools
import glob
import hashlib
import importlib
import itertools
import os
import pathlib
import re
import shutil
import sys
import tempfile
import warnings
from io import (
    BufferedRandom,
    BufferedReader,
    BufferedWriter,
    FileIO,
    TextIOWrapper,
)
from types import ModuleType

with contextlib.suppress(ImportError):
    import win32security  # type: ignore[import-not-found]

with contextlib.suppress(ImportError):
    import pwd

with contextlib.suppress(ImportError):
    import grp

from typing import (
    TYPE_CHECKING,
    IO,
    Any,
    BinaryIO,
    Callable,
    Generator,
    Iterable,
    Iterator,
    overload,
)

if TYPE_CHECKING:
    from typing_extensions import Literal, Never, Self, Union
    from _typeshed import (
        OpenBinaryMode,
        OpenBinaryModeReading,
        OpenBinaryModeUpdating,
        OpenBinaryModeWriting,
        OpenTextMode,
        ExcInfo,
    )

    _Match = Union[str, Callable[[str], bool], None]
    _CopyFn = Callable[[str, str], object]
    _IgnoreFn = Callable[[str, list[str]], Iterable[str]]
    _OnErrorCallback = Callable[[Callable[..., Any], str, ExcInfo], object]
    _OnExcCallback = Callable[[Callable[..., Any], str, BaseException], object]


from . import classes, masks, matchers
from .compat.py38 import removeprefix, removesuffix

__all__ = ['Path', 'TempDir']

LINESEPS = ['\r\n', '\r', '\n']
U_LINESEPS = LINESEPS + ['\u0085', '\u2028', '\u2029']
B_NEWLINE = re.compile('|'.join(LINESEPS).encode())
U_NEWLINE = re.compile('|'.join(U_LINESEPS))
B_NL_END = re.compile(B_NEWLINE.pattern + b'$')
U_NL_END = re.compile(U_NEWLINE.pattern + '$')

_default_linesep = object()


def _make_timestamp_ns(value: float | datetime.datetime) -> int:
    timestamp_s = value if isinstance(value, (float, int)) else value.timestamp()
    return int(timestamp_s * 10**9)


class TreeWalkWarning(Warning):
    pass


class Traversal:
    """
    Wrap a walk result to customize the traversal.

    `follow` is a function that takes an item and returns
    True if that item should be followed and False otherwise.

    For example, to avoid traversing into directories that
    begin with `.`:

    >>> traverse = Traversal(lambda dir: not dir.startswith('.'))
    >>> items = list(traverse(Path('.').walk()))

    Directories beginning with `.` will appear in the results, but
    their children will not.

    >>> dot_dir = next(item for item in items if item.is_dir() and item.startswith('.'))
    >>> any(item.parent == dot_dir for item in items)
    False
    """

    def __init__(self, follow: Callable[[Path], bool]):
        self.follow = follow

    def __call__(
        self, walker: Generator[Path, Callable[[], bool] | None, None]
    ) -> Iterator[Path]:
        traverse = None
        while True:
            try:
                item = walker.send(traverse)
            except StopIteration:
                return
            yield item

            traverse = functools.partial(self.follow, item)


def _strip_newlines(lines: Iterable[str]) -> Iterator[str]:
    r"""
    >>> list(_strip_newlines(['Hello World\r\n', 'foo']))
    ['Hello World', 'foo']
    """
    return (U_NL_END.sub('', line) for line in lines)


class Path(str):
    """
    Represents a filesystem path.

    For documentation on individual methods, consult their
    counterparts in :mod:`os.path`.

    Some methods are additionally included from :mod:`shutil`.
    The functions are linked directly into the class namespace
    such that they will be bound to the Path instance. For example,
    ``Path(src).copy(target)`` is equivalent to
    ``shutil.copy(src, target)``. Therefore, when referencing
    the docs for these methods, assume `src` references `self`,
    the Path instance.
    """

    module: ModuleType = os.path
    """ The path module to use for path operations.

    .. seealso:: :mod:`os.path`
    """

    def __new__(cls, other: Any = '.') -> Self:
        return super().__new__(cls, other)

    def __init__(self, other: Any = '.') -> None:
        if other is None:
            raise TypeError("Invalid initial value for path: None")
        self._validate()

    def _validate(self) -> None:
        pass

    @classmethod
    @functools.lru_cache
    def using_module(cls, module: ModuleType) -> type[Self]:
        subclass_name = cls.__name__ + '_' + module.__name__
        bases = (cls,)
        ns = {'module': module}
        return type(subclass_name, bases, ns)

    @classes.ClassProperty
    @classmethod
    def _next_class(cls) -> type[Self]:
        """
        What class should be used to construct new instances from this class
        """
        return cls

    # --- Special Python methods.

    def __repr__(self) -> str:
        return f'{type(self).__name__}({super().__repr__()})'

    # Adding a Path and a string yields a Path.
    def __add__(self, more: str) -> Self:
        return self._next_class(super().__add__(more))

    def __radd__(self, other: str) -> Self:
        return self._next_class(other.__add__(self))

    # The / operator joins Paths.
    def __truediv__(self, rel: str) -> Self:
        """fp.__truediv__(rel) == fp / rel == fp.joinpath(rel)

        Join two path components, adding a separator character if
        needed.

        .. seealso:: :func:`os.path.join`
        """
        return self._next_class(self.module.join(self, rel))

    # The / operator joins Paths the other way around
    def __rtruediv__(self, rel: str) -> Self:
        """fp.__rtruediv__(rel) == rel / fp

        Join two path components, adding a separator character if
        needed.

        .. seealso:: :func:`os.path.join`
        """
        return self._next_class(self.module.join(rel, self))

    def __enter__(self) -> Self:
        self._old_dir = self.cwd()
        os.chdir(self)
        return self

    def __exit__(self, *_) -> None:
        os.chdir(self._old_dir)

    @classmethod
    def cwd(cls):
        """Return the current working directory as a path object.

        .. seealso:: :func:`os.getcwd`
        """
        return cls(os.getcwd())

    @classmethod
    def home(cls) -> Path:
        return cls(os.path.expanduser('~'))

    #
    # --- Operations on Path strings.

    def absolute(self) -> Self:
        """.. seealso:: :func:`os.path.abspath`"""
        return self._next_class(self.module.abspath(self))

    def normcase(self) -> Self:
        """.. seealso:: :func:`os.path.normcase`"""
        return self._next_class(self.module.normcase(self))

    def normpath(self) -> Self:
        """.. seealso:: :func:`os.path.normpath`"""
        return self._next_class(self.module.normpath(self))

    def realpath(self) -> Self:
        """.. seealso:: :func:`os.path.realpath`"""
        return self._next_class(self.module.realpath(self))

    def expanduser(self) -> Self:
        """.. seealso:: :func:`os.path.expanduser`"""
        return self._next_class(self.module.expanduser(self))

    def expandvars(self) -> Self:
        """.. seealso:: :func:`os.path.expandvars`"""
        return self._next_class(self.module.expandvars(self))

    def dirname(self) -> Self:
        """.. seealso:: :attr:`parent`, :func:`os.path.dirname`"""
        return self._next_class(self.module.dirname(self))

    def basename(self) -> Self:
        """.. seealso:: :attr:`name`, :func:`os.path.basename`"""
        return self._next_class(self.module.basename(self))

    def expand(self) -> Self:
        """Clean up a filename by calling :meth:`expandvars()`,
        :meth:`expanduser()`, and :meth:`normpath()` on it.

        This is commonly everything needed to clean up a filename
        read from a configuration file, for example.
        """
        return self.expandvars().expanduser().normpath()

    @property
    def stem(self) -> str:
        """The same as :meth:`name`, but with one file extension stripped off.

        >>> Path('/home/guido/python.tar.gz').stem
        'python.tar'
        """
        base, _ = self.module.splitext(self.name)
        return base

    def with_stem(self, stem: str) -> Self:
        """Return a new path with the stem changed.

        >>> Path('/home/guido/python.tar.gz').with_stem("foo")
        Path('/home/guido/foo.gz')
        """
        return self.with_name(stem + self.suffix)

    @property
    def suffix(self) -> Self:
        """The file extension, for example ``'.py'``."""
        _, suffix = self.module.splitext(self)
        return suffix

    def with_suffix(self, suffix: str) -> Self:
        """Return a new path with the file suffix changed (or added, if none)

        >>> Path('/home/guido/python.tar.gz').with_suffix(".foo")
        Path('/home/guido/python.tar.foo')

        >>> Path('python').with_suffix('.zip')
        Path('python.zip')

        >>> Path('filename.ext').with_suffix('zip')
        Traceback (most recent call last):
        ...
        ValueError: Invalid suffix 'zip'
        """
        if not suffix.startswith('.'):
            raise ValueError(f"Invalid suffix {suffix!r}")
        return self.stripext() + suffix

    @property
    def drive(self) -> Self:
        """The drive specifier, for example ``'C:'``.

        This is always empty on systems that don't use drive specifiers.
        """
        drive, _ = self.module.splitdrive(self)
        return self._next_class(drive)

    @property
    def parent(self) -> Self:
        """This path's parent directory, as a new Path object.

        For example,
        ``Path('/usr/local/lib/libpython.so').parent ==
        Path('/usr/local/lib')``

        .. seealso:: :meth:`dirname`, :func:`os.path.dirname`
        """
        return self.dirname()

    @property
    def name(self) -> Self:
        """The name of this file or directory without the full path.

        For example,
        ``Path('/usr/local/lib/libpython.so').name == 'libpython.so'``

        .. seealso:: :meth:`basename`, :func:`os.path.basename`
        """
        return self.basename()

    def with_name(self, name: str) -> Self:
        """Return a new path with the name changed.

        >>> Path('/home/guido/python.tar.gz').with_name("foo.zip")
        Path('/home/guido/foo.zip')
        """
        return self._next_class(removesuffix(self, self.name) + name)

    def splitpath(self) -> tuple[Self, str]:
        """Return two-tuple of ``.parent``, ``.name``.

        .. seealso:: :attr:`parent`, :attr:`name`, :func:`os.path.split`
        """
        parent, child = self.module.split(self)
        return self._next_class(parent), child

    def splitdrive(self) -> tuple[Self, Self]:
        """Return two-tuple of ``.drive`` and rest without drive.

        Split the drive specifier from this path.  If there is
        no drive specifier, :samp:`{p.drive}` is empty, so the return value
        is simply ``(Path(''), p)``.  This is always the case on Unix.

        .. seealso:: :func:`os.path.splitdrive`
        """
        drive, rel = self.module.splitdrive(self)
        return self._next_class(drive), self._next_class(rel)

    def splitext(self) -> tuple[Self, str]:
        """Return two-tuple of ``.stripext()`` and ``.ext``.

        Split the filename extension from this path and return
        the two parts.  Either part may be empty.

        The extension is everything from ``'.'`` to the end of the
        last path segment.  This has the property that if
        ``(a, b) == p.splitext()``, then ``a + b == p``.

        .. seealso:: :func:`os.path.splitext`
        """
        filename, ext = self.module.splitext(self)
        return self._next_class(filename), ext

    def stripext(self) -> Self:
        """Remove one file extension from the path.

        For example, ``Path('/home/guido/python.tar.gz').stripext()``
        returns ``Path('/home/guido/python.tar')``.
        """
        return self.splitext()[0]

    @classes.multimethod
    def joinpath(cls, first: str, *others: str) -> Self:
        """
        Join first to zero or more :class:`Path` components,
        adding a separator character (:samp:`{first}.module.sep`)
        if needed.  Returns a new instance of
        :samp:`{first}._next_class`.

        .. seealso:: :func:`os.path.join`
        """
        return cls._next_class(cls.module.join(first, *others))

    def splitall(self) -> list[Self | str]:
        r"""Return a list of the path components in this path.

        The first item in the list will be a Path.  Its value will be
        either :data:`os.curdir`, :data:`os.pardir`, empty, or the root
        directory of this path (for example, ``'/'`` or ``'C:\\'``).  The
        other items in the list will be strings.

        ``Path.joinpath(*result)`` will yield the original path.

        >>> Path('/foo/bar/baz').splitall()
        [Path('/'), 'foo', 'bar', 'baz']
        """
        return list(self._parts())

    def parts(self) -> tuple[Self | str, ...]:
        """
        >>> Path('/foo/bar/baz').parts()
        (Path('/'), 'foo', 'bar', 'baz')
        """
        return tuple(self._parts())

    def _parts(self) -> Iterator[Self | str]:
        return reversed(tuple(self._parts_iter()))

    def _parts_iter(self) -> Iterator[Self | str]:
        loc = self
        while loc != os.curdir and loc != os.pardir:
            prev = loc
            loc, child = prev.splitpath()
            if loc == prev:
                break
            yield child
        yield loc

    def relpath(self, start: str = '.') -> Self:
        """Return this path as a relative path,
        based from `start`, which defaults to the current working directory.
        """
        cwd = self._next_class(start)
        return cwd.relpathto(self)

    def relpathto(self, dest: str) -> Self:
        """Return a relative path from `self` to `dest`.

        If there is no relative path from `self` to `dest`, for example if
        they reside on different drives in Windows, then this returns
        ``dest.absolute()``.
        """
        origin = self.absolute()
        dest_path = self._next_class(dest).absolute()

        orig_list = origin.normcase().splitall()
        # Don't normcase dest!  We want to preserve the case.
        dest_list = dest_path.splitall()

        if orig_list[0] != self.module.normcase(dest_list[0]):
            # Can't get here from there.
            return dest_path

        # Find the location where the two paths start to differ.
        i = 0
        for start_seg, dest_seg in zip(orig_list, dest_list):
            if start_seg != self.module.normcase(dest_seg):
                break
            i += 1

        # Now i is the point where the two paths diverge.
        # Need a certain number of "os.pardir"s to work up
        # from the origin to the point of divergence.
        segments = [os.pardir] * (len(orig_list) - i)
        # Need to add the diverging part of dest_list.
        segments += dest_list[i:]
        if len(segments) == 0:
            # If they happen to be identical, use os.curdir.
            relpath = os.curdir
        else:
            relpath = self.module.join(*segments)
        return self._next_class(relpath)

    # --- Listing, searching, walking, and matching

    def iterdir(self, match: _Match = None) -> Iterator[Self]:
        """Yields items in this directory.

        Use :meth:`files` or :meth:`dirs` instead if you want a listing
        of just files or just subdirectories.

        The elements of the list are Path objects.

        With the optional `match` argument, a callable,
        only return items whose names match the given pattern.

        .. seealso:: :meth:`files`, :meth:`dirs`
        """
        match = matchers.load(match)
        return filter(match, (self / child for child in os.listdir(self)))

    def dirs(self, match: _Match = None) -> list[Self]:
        """List of this directory's subdirectories.

        The elements of the list are Path objects.
        This does not walk recursively into subdirectories
        (but see :meth:`walkdirs`).

        Accepts parameters to :meth:`iterdir`.
        """
        return [p for p in self.iterdir(match) if p.is_dir()]

    def files(self, match: _Match = None) -> list[Self]:
        """List of the files in self.

        The elements of the list are Path objects.
        This does not walk into subdirectories (see :meth:`walkfiles`).

        Accepts parameters to :meth:`iterdir`.
        """

        return [p for p in self.iterdir(match) if p.is_file()]

    def walk(
        self, match: _Match = None, errors: str = 'strict'
    ) -> Generator[Self, Callable[[], bool] | None, None]:
        """Iterator over files and subdirs, recursively.

        The iterator yields Path objects naming each child item of
        this directory and its descendants.  This requires that
        ``D.is_dir()``.

        This performs a depth-first traversal of the directory tree.
        Each directory is returned just before all its children.

        The `errors=` keyword argument controls behavior when an
        error occurs.  The default is ``'strict'``, which causes an
        exception.  Other allowed values are ``'warn'`` (which
        reports the error via :func:`warnings.warn()`), and ``'ignore'``.
        `errors` may also be an arbitrary callable taking a msg parameter.
        """

        error_fn = Handlers._resolve(errors)
        match = matchers.load(match)

        try:
            childList = self.iterdir()
        except Exception as exc:
            error_fn(f"Unable to list directory '{self}': {exc}")
            return

        for child in childList:
            traverse = None
            if match(child):
                traverse = yield child
            traverse = traverse or child.is_dir
            try:
                do_traverse = traverse()
            except Exception as exc:
                error_fn(f"Unable to access '{child}': {exc}")
                continue

            if do_traverse:
                yield from child.walk(errors=error_fn, match=match)  # type: ignore[arg-type]

    def walkdirs(self, match: _Match = None, errors: str = 'strict') -> Iterator[Self]:
        """Iterator over subdirs, recursively."""
        return (item for item in self.walk(match, errors) if item.is_dir())

    def walkfiles(self, match: _Match = None, errors: str = 'strict') -> Iterator[Self]:
        """Iterator over files, recursively."""
        return (item for item in self.walk(match, errors) if item.is_file())

    def fnmatch(
        self, pattern: str, normcase: Callable[[str], str] | None = None
    ) -> bool:
        """Return ``True`` if `self.name` matches the given `pattern`.

        `pattern` - A filename pattern with wildcards,
            for example ``'*.py'``. If the pattern contains a `normcase`
            attribute, it is applied to the name and path prior to comparison.

        `normcase` - (optional) A function used to normalize the pattern and
            filename before matching. Defaults to normcase from
            ``self.module``, :func:`os.path.normcase`.

        .. seealso:: :func:`fnmatch.fnmatch`
        """
        default_normcase = getattr(pattern, 'normcase', self.module.normcase)
        normcase = normcase or default_normcase
        name = normcase(self.name)
        pattern = normcase(pattern)
        return fnmatch.fnmatchcase(name, pattern)

    def glob(self, pattern: str) -> list[Self]:
        """Return a list of Path objects that match the pattern.

        `pattern` - a path relative to this directory, with wildcards.

        For example, ``Path('/users').glob('*/bin/*')`` returns a list
        of all the files users have in their :file:`bin` directories.

        .. seealso:: :func:`glob.glob`

        .. note:: Glob is **not** recursive, even when using ``**``.
                  To do recursive globbing see :func:`walk`,
                  :func:`walkdirs` or :func:`walkfiles`.
        """
        cls = self._next_class
        return [cls(s) for s in glob.glob(self / pattern)]

    def iglob(self, pattern: str) -> Iterator[Self]:
        """Return an iterator of Path objects that match the pattern.

        `pattern` - a path relative to this directory, with wildcards.

        For example, ``Path('/users').iglob('*/bin/*')`` returns an
        iterator of all the files users have in their :file:`bin`
        directories.

        .. seealso:: :func:`glob.iglob`

        .. note:: Glob is **not** recursive, even when using ``**``.
                  To do recursive globbing see :func:`walk`,
                  :func:`walkdirs` or :func:`walkfiles`.
        """
        cls = self._next_class
        return (cls(s) for s in glob.iglob(self / pattern))

    #
    # --- Reading or writing an entire file at once.

    @overload
    def open(
        self,
        mode: OpenTextMode = ...,
        buffering: int = ...,
        encoding: str | None = ...,
        errors: str | None = ...,
        newline: str | None = ...,
        closefd: bool = True,
        opener: Callable[[str, int], int] | None = ...,
    ) -> TextIOWrapper: ...
    @overload
    def open(
        self,
        mode: OpenBinaryMode,
        buffering: Literal[0],
        encoding: None = ...,
        errors: None = ...,
        newline: None = ...,
        closefd: bool = True,
        opener: Callable[[str, int], int] | None = ...,
    ) -> FileIO: ...
    @overload
    def open(
        self,
        mode: OpenBinaryModeUpdating,
        buffering: Literal[-1, 1] = ...,
        encoding: None = ...,
        errors: None = ...,
        newline: None = ...,
        closefd: bool = True,
        opener: Callable[[str, int], int] | None = ...,
    ) -> BufferedRandom: ...
    @overload
    def open(
        self,
        mode: OpenBinaryModeWriting,
        buffering: Literal[-1, 1] = ...,
        encoding: None = ...,
        errors: None = ...,
        newline: None = ...,
        closefd: bool = True,
        opener: Callable[[str, int], int] | None = ...,
    ) -> BufferedWriter: ...
    @overload
    def open(
        self,
        mode: OpenBinaryModeReading,
        buffering: Literal[-1, 1] = ...,
        encoding: None = ...,
        errors: None = ...,
        newline: None = ...,
        closefd: bool = True,
        opener: Callable[[str, int], int] | None = ...,
    ) -> BufferedReader: ...
    @overload
    def open(
        self,
        mode: OpenBinaryMode,
        buffering: int = ...,
        encoding: None = ...,
        errors: None = ...,
        newline: None = ...,
        closefd: bool = True,
        opener: Callable[[str, int], int] | None = ...,
    ) -> BinaryIO: ...
    @overload
    def open(
        self,
        mode: str,
        buffering: int = ...,
        encoding: str | None = ...,
        errors: str | None = ...,
        newline: str | None = ...,
        closefd: bool = True,
        opener: Callable[[str, int], int] | None = ...,
    ) -> IO[Any]: ...
    def open(self, *args, **kwargs):
        """Open this file and return a corresponding file object.

        Keyword arguments work as in :func:`io.open`.  If the file cannot be
        opened, an :class:`OSError` is raised.
        """
        return open(self, *args, **kwargs)

    def bytes(self) -> builtins.bytes:
        """Open this file, read all bytes, return them as a string."""
        with self.open('rb') as f:
            return f.read()

    @overload
    def chunks(
        self,
        size: int,
        mode: OpenTextMode = ...,
        buffering: int = ...,
        encoding: str | None = ...,
        errors: str | None = ...,
        newline: str | None = ...,
        closefd: bool = ...,
        opener: Callable[[str, int], int] | None = ...,
    ) -> Iterator[str]: ...
    @overload
    def chunks(
        self,
        size: int,
        mode: OpenBinaryMode,
        buffering: int = ...,
        encoding: str | None = ...,
        errors: str | None = ...,
        newline: str | None = ...,
        closefd: bool = ...,
        opener: Callable[[str, int], int] | None = ...,
    ) -> Iterator[builtins.bytes]: ...
    @overload
    def chunks(
        self,
        size: int,
        mode: str,
        buffering: int = ...,
        encoding: str | None = ...,
        errors: str | None = ...,
        newline: str | None = ...,
        closefd: bool = ...,
        opener: Callable[[str, int], int] | None = ...,
    ) -> Iterator[str | builtins.bytes]: ...
    def chunks(self, size, *args, **kwargs):
        """Returns a generator yielding chunks of the file, so it can
         be read piece by piece with a simple for loop.

        Any argument you pass after `size` will be passed to :meth:`open`.

        :example:

            >>> hash = hashlib.md5()
            >>> for chunk in Path("NEWS.rst").chunks(8192, mode='rb'):
            ...     hash.update(chunk)

         This will read the file by chunks of 8192 bytes.
        """
        with self.open(*args, **kwargs) as f:
            yield from iter(lambda: f.read(size) or None, None)

    def write_bytes(self, bytes: builtins.bytes, append: bool = False) -> None:
        """Open this file and write the given bytes to it.

        Default behavior is to overwrite any existing file.
        Call ``p.write_bytes(bytes, append=True)`` to append instead.
        """
        with self.open('ab' if append else 'wb') as f:
            f.write(bytes)

    def read_text(self, encoding: str | None = None, errors: str | None = None) -> str:
        r"""Open this file, read it in, return the content as a string.

        Optional parameters are passed to :meth:`open`.

        .. seealso:: :meth:`lines`
        """
        with self.open(encoding=encoding, errors=errors) as f:
            return f.read()

    def read_bytes(self) -> builtins.bytes:
        r"""Return the contents of this file as bytes."""
        with self.open(mode='rb') as f:
            return f.read()

    def write_text(
        self,
        text: str,
        encoding: str | None = None,
        errors: str = 'strict',
        linesep: str | None = os.linesep,
        append: bool = False,
    ) -> None:
        r"""Write the given text to this file.

        The default behavior is to overwrite any existing file;
        to append instead, use the `append=True` keyword argument.

        There are two differences between :meth:`write_text` and
        :meth:`write_bytes`: newline handling and Unicode handling.
        See below.

        Parameters:

          `text` - str - The text to be written.

          `encoding` - str - The text encoding used.

          `errors` - str - How to handle Unicode encoding errors.
              Default is ``'strict'``.  See ``help(unicode.encode)`` for the
              options.  Ignored if `text` isn't a Unicode string.

          `linesep` - keyword argument - str/unicode - The sequence of
              characters to be used to mark end-of-line.  The default is
              :data:`os.linesep`.  Specify ``None`` to
              use newlines unmodified.

          `append` - keyword argument - bool - Specifies what to do if
              the file already exists (``True``: append to the end of it;
              ``False``: overwrite it).  The default is ``False``.


        --- Newline handling.

        ``write_text()`` converts all standard end-of-line sequences
        (``'\n'``, ``'\r'``, and ``'\r\n'``) to your platform's default
        end-of-line sequence (see :data:`os.linesep`; on Windows, for example,
        the end-of-line marker is ``'\r\n'``).

        To override the platform's default, pass the `linesep=`
        keyword argument. To preserve the newlines as-is, pass
        ``linesep=None``.

        This handling applies to Unicode text and bytes, except
        with Unicode, additional non-ASCII newlines are recognized:
        ``\x85``, ``\r\x85``, and ``\u2028``.

        --- Unicode

        `text` is written using the
        specified `encoding` (or the default encoding if `encoding`
        isn't specified).  The `errors` argument applies only to this
        conversion.
        """
        if linesep is not None:
            text = U_NEWLINE.sub(linesep, text)
        bytes = text.encode(encoding or sys.getdefaultencoding(), errors)
        self.write_bytes(bytes, append=append)

    def lines(
        self,
        encoding: str | None = None,
        errors: str | None = None,
        retain: bool = True,
    ) -> list[str]:
        r"""Open this file, read all lines, return them in a list.

        Optional arguments:
            `encoding` - The Unicode encoding (or character set) of
                the file.  The default is ``None``, meaning use
                ``locale.getpreferredencoding()``.
            `errors` - How to handle Unicode errors; see
                `open <https://docs.python.org/3/library/functions.html#open>`_
                for the options.  Default is ``None`` meaning "strict".
            `retain` - If ``True`` (default), retain newline characters,
                but translate all newline
                characters to ``\n``.  If ``False``, newline characters are
                omitted.
        """
        text = U_NEWLINE.sub('\n', self.read_text(encoding, errors))
        return text.splitlines(retain)

    def write_lines(
        self,
        lines: list[str],
        encoding: str | None = None,
        errors: str = 'strict',
        *,
        append: bool = False,
    ):
        r"""Write the given lines of text to this file.

        By default this overwrites any existing file at this path.

        Puts a platform-specific newline sequence on every line.

            `lines` - A list of strings.

            `encoding` - A Unicode encoding to use.  This applies only if
                `lines` contains any Unicode strings.

            `errors` - How to handle errors in Unicode encoding.  This
                also applies only to Unicode strings.

        Use the keyword argument ``append=True`` to append lines to the
        file.  The default is to overwrite the file.
        """
        mode = 'a' if append else 'w'
        with self.open(mode, encoding=encoding, errors=errors, newline='') as f:
            f.writelines(self._replace_linesep(lines))

    @staticmethod
    def _replace_linesep(lines: Iterable[str]) -> Iterator[str]:
        return (line + os.linesep for line in _strip_newlines(lines))

    def read_md5(self) -> builtins.bytes:
        """Calculate the md5 hash for this file.

        This reads through the entire file.

        .. seealso:: :meth:`read_hash`
        """
        return self.read_hash('md5')

    def _hash(self, hash_name: str) -> hashlib._Hash:
        """Returns a hash object for the file at the current path.

        `hash_name` should be a hash algo name (such as ``'md5'``
        or ``'sha1'``) that's available in the :mod:`hashlib` module.
        """
        m = hashlib.new(hash_name)
        for chunk in self.chunks(8192, mode="rb"):
            m.update(chunk)
        return m

    def read_hash(self, hash_name) -> builtins.bytes:
        """Calculate given hash for this file.

        List of supported hashes can be obtained from :mod:`hashlib` package.
        This reads the entire file.

        .. seealso:: :meth:`hashlib.hash.digest`
        """
        return self._hash(hash_name).digest()

    def read_hexhash(self, hash_name) -> str:
        """Calculate given hash for this file, returning hexdigest.

        List of supported hashes can be obtained from :mod:`hashlib` package.
        This reads the entire file.

        .. seealso:: :meth:`hashlib.hash.hexdigest`
        """
        return self._hash(hash_name).hexdigest()

    # --- Methods for querying the filesystem.
    # N.B. On some platforms, the os.path functions may be implemented in C
    # (e.g. isdir on Windows, Python 3.2.2), and compiled functions don't get
    # bound. Playing it safe and wrapping them all in method calls.

    def isabs(self) -> bool:
        """
        >>> Path('.').isabs()
        False

        .. seealso:: :func:`os.path.isabs`
        """
        return self.module.isabs(self)

    def exists(self) -> bool:
        """.. seealso:: :func:`os.path.exists`"""
        return self.module.exists(self)

    def is_dir(self) -> bool:
        """.. seealso:: :func:`os.path.isdir`"""
        return self.module.isdir(self)

    def is_file(self) -> bool:
        """.. seealso:: :func:`os.path.isfile`"""
        return self.module.isfile(self)

    def islink(self) -> bool:
        """.. seealso:: :func:`os.path.islink`"""
        return self.module.islink(self)

    def ismount(self) -> bool:
        """
        >>> Path('.').ismount()
        False

        .. seealso:: :func:`os.path.ismount`
        """
        return self.module.ismount(self)

    def samefile(self, other: str) -> bool:
        """.. seealso:: :func:`os.path.samefile`"""
        return self.module.samefile(self, other)

    def getatime(self) -> float:
        """.. seealso:: :attr:`atime`, :func:`os.path.getatime`"""
        return self.module.getatime(self)

    def set_atime(self, value: float | datetime.datetime) -> None:
        mtime_ns = self.stat().st_atime_ns
        self.utime(ns=(_make_timestamp_ns(value), mtime_ns))

    @property
    def atime(self) -> float:
        """
        Last access time of the file.

        >>> Path('.').atime > 0
        True

        Allows setting:

        >>> some_file = Path(getfixture('tmp_path')).joinpath('file.txt').touch()
        >>> MST = datetime.timezone(datetime.timedelta(hours=-7))
        >>> some_file.atime = datetime.datetime(1976, 5, 7, 10, tzinfo=MST)
        >>> some_file.atime
        200336400.0

        .. seealso:: :meth:`getatime`, :func:`os.path.getatime`
        """
        return self.getatime()

    @atime.setter
    def atime(self, value: float | datetime.datetime) -> None:
        self.set_atime(value)

    def getmtime(self) -> float:
        """.. seealso:: :attr:`mtime`, :func:`os.path.getmtime`"""
        return self.module.getmtime(self)

    def set_mtime(self, value: float | datetime.datetime) -> None:
        atime_ns = self.stat().st_atime_ns
        self.utime(ns=(atime_ns, _make_timestamp_ns(value)))

    @property
    def mtime(self) -> float:
        """
        Last modified time of the file.

        Allows setting:

        >>> some_file = Path(getfixture('tmp_path')).joinpath('file.txt').touch()
        >>> MST = datetime.timezone(datetime.timedelta(hours=-7))
        >>> some_file.mtime = datetime.datetime(1976, 5, 7, 10, tzinfo=MST)
        >>> some_file.mtime
        200336400.0

        .. seealso:: :meth:`getmtime`, :func:`os.path.getmtime`
        """
        return self.getmtime()

    @mtime.setter
    def mtime(self, value: float | datetime.datetime) -> None:
        self.set_mtime(value)

    def getctime(self) -> float:
        """.. seealso:: :attr:`ctime`, :func:`os.path.getctime`"""
        return self.module.getctime(self)

    @property
    def ctime(self) -> float:
        """Creation time of the file.

        .. seealso:: :meth:`getctime`, :func:`os.path.getctime`
        """
        return self.getctime()

    def getsize(self) -> int:
        """.. seealso:: :attr:`size`, :func:`os.path.getsize`"""
        return self.module.getsize(self)

    @property
    def size(self) -> int:
        """Size of the file, in bytes.

        .. seealso:: :meth:`getsize`, :func:`os.path.getsize`
        """
        return self.getsize()

    @property
    def permissions(self) -> masks.Permissions:
        """
        Permissions.

        >>> perms = Path('.').permissions
        >>> isinstance(perms, int)
        True
        >>> set(perms.symbolic) <= set('rwx-')
        True
        >>> perms.symbolic
        'r...'
        """
        return masks.Permissions(self.stat().st_mode)

    def access(
        self,
        mode: int,
        *,
        dir_fd: int | None = None,
        effective_ids: bool = False,
        follow_symlinks: bool = True,
    ) -> bool:
        """
        Return does the real user have access to this path.

        >>> Path('.').access(os.F_OK)
        True

        .. seealso:: :func:`os.access`
        """
        return os.access(
            self,
            mode,
            dir_fd=dir_fd,
            effective_ids=effective_ids,
            follow_symlinks=follow_symlinks,
        )

    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        """
        Perform a ``stat()`` system call on this path.

        >>> Path('.').stat()
        os.stat_result(...)

        .. seealso:: :meth:`lstat`, :func:`os.stat`
        """
        return os.stat(self, follow_symlinks=follow_symlinks)

    def lstat(self) -> os.stat_result:
        """
        Like :meth:`stat`, but do not follow symbolic links.

        >>> Path('.').lstat() == Path('.').stat()
        True

        .. seealso:: :meth:`stat`, :func:`os.lstat`
        """
        return os.lstat(self)

    if sys.platform == "win32":

        def get_owner(self) -> str:  # pragma: nocover
            r"""
            Return the name of the owner of this file or directory. Follow
            symbolic links.

            Return a name of the form ``DOMAIN\User Name``; may be a group.

            .. seealso:: :attr:`owner`
            """
            if "win32security" not in globals():
                raise NotImplementedError("Ownership not available on this platform.")

            desc = win32security.GetFileSecurity(
                self, win32security.OWNER_SECURITY_INFORMATION
            )
            sid = desc.GetSecurityDescriptorOwner()
            account, domain, typecode = win32security.LookupAccountSid(None, sid)
            return domain + '\\' + account

    else:

        def get_owner(self) -> str:  # pragma: nocover
            """
            Return the name of the owner of this file or directory. Follow
            symbolic links.

            .. seealso:: :attr:`owner`
            """
            st = self.stat()
            return pwd.getpwuid(st.st_uid).pw_name

    @property
    def owner(self) -> str:
        """Name of the owner of this file or directory.

        .. seealso:: :meth:`get_owner`"""
        return self.get_owner()

    if sys.platform != "win32":  # pragma: no cover

        def group(self, *, follow_symlinks: bool = True) -> str:
            """
            Return the group name of the file gid.
            """
            gid = self.stat(follow_symlinks=follow_symlinks).st_gid
            return grp.getgrgid(gid).gr_name

        def statvfs(self) -> os.statvfs_result:
            """Perform a ``statvfs()`` system call on this path.

            .. seealso:: :func:`os.statvfs`
            """
            return os.statvfs(self)

        def pathconf(self, name: str | int) -> int:
            """.. seealso:: :func:`os.pathconf`"""
            return os.pathconf(self, name)

    #
    # --- Modifying operations on files and directories

    @overload
    def utime(
        self,
        times: tuple[int, int] | tuple[float, float] | None = None,
        *,
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> Self: ...
    @overload
    def utime(
        self,
        times: tuple[int, int] | tuple[float, float] | None = None,
        *,
        ns: tuple[int, int],
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> Self: ...

    def utime(self, *args, **kwargs) -> Self:
        """Set the access and modified times of this file.

        .. seealso:: :func:`os.utime`
        """
        os.utime(self, *args, **kwargs)
        return self

    def chmod(self, mode: str | int) -> Self:
        """
        Set the mode. May be the new mode (os.chmod behavior) or a `symbolic
        mode <http://en.wikipedia.org/wiki/Chmod#Symbolic_modes>`_.

        >>> a_file = Path(getfixture('tmp_path')).joinpath('afile.txt').touch()
        >>> a_file.chmod(0o700)
        Path(...
        >>> a_file.chmod('u+x')
        Path(...

        .. seealso:: :func:`os.chmod`
        """
        if isinstance(mode, str):
            mask = masks.compound(mode)
            mode = mask(self.stat().st_mode)
        os.chmod(self, mode)
        return self

    if sys.platform != "win32":

        def chown(self, uid: str | int = -1, gid: str | int = -1) -> Self:
            """
            Change the owner and group by names or numbers.

            .. seealso:: :func:`os.chown`
            """

            def resolve_uid(uid: str | int) -> int:
                return uid if isinstance(uid, int) else pwd.getpwnam(uid).pw_uid

            def resolve_gid(gid: str | int) -> int:
                return gid if isinstance(gid, int) else grp.getgrnam(gid).gr_gid

            os.chown(self, resolve_uid(uid), resolve_gid(gid))
            return self

    def rename(self, new: str) -> Self:
        """.. seealso:: :func:`os.rename`"""
        os.rename(self, new)
        return self._next_class(new)

    def renames(self, new: str) -> Self:
        """.. seealso:: :func:`os.renames`"""
        os.renames(self, new)
        return self._next_class(new)

    def replace(self, target_or_old: str, *args) -> Self:
        """
        Replace a path or substitute substrings.

        Implements both pathlib.Path.replace and str.replace.

        If only a target is supplied, rename this path to the target path,
        overwriting if that path exists.

        >>> dest = Path(getfixture('tmp_path'))
        >>> orig = dest.joinpath('foo').touch()
        >>> new = orig.replace(dest.joinpath('fee'))
        >>> orig.exists()
        False
        >>> new.exists()
        True

        ..seealso:: :meth:`pathlib.Path.replace`

        If a second parameter is supplied, perform a textual replacement.

        >>> Path('foo').replace('o', 'e')
        Path('fee')
        >>> Path('foo').replace('o', 'l', 1)
        Path('flo')

        ..seealso:: :meth:`str.replace`
        """
        return self._next_class(
            super().replace(target_or_old, *args)
            if args
            else pathlib.Path(self).replace(target_or_old)
        )

    #
    # --- Create/delete operations on directories

    def mkdir(self, mode: int = 0o777) -> Self:
        """.. seealso:: :func:`os.mkdir`"""
        os.mkdir(self, mode)
        return self

    def mkdir_p(self, mode: int = 0o777) -> Self:
        """Like :meth:`mkdir`, but does not raise an exception if the
        directory already exists."""
        with contextlib.suppress(FileExistsError):
            self.mkdir(mode)
        return self

    def makedirs(self, mode: int = 0o777) -> Self:
        """.. seealso:: :func:`os.makedirs`"""
        os.makedirs(self, mode)
        return self

    def makedirs_p(self, mode: int = 0o777) -> Self:
        """Like :meth:`makedirs`, but does not raise an exception if the
        directory already exists."""
        with contextlib.suppress(FileExistsError):
            self.makedirs(mode)
        return self

    def rmdir(self) -> Self:
        """.. seealso:: :func:`os.rmdir`"""
        os.rmdir(self)
        return self

    def rmdir_p(self) -> Self:
        """Like :meth:`rmdir`, but does not raise an exception if the
        directory is not empty or does not exist."""
        suppressed = FileNotFoundError, FileExistsError, DirectoryNotEmpty
        with contextlib.suppress(*suppressed):
            with DirectoryNotEmpty.translate():
                self.rmdir()
        return self

    def removedirs(self) -> Self:
        """.. seealso:: :func:`os.removedirs`"""
        os.removedirs(self)
        return self

    def removedirs_p(self) -> Self:
        """Like :meth:`removedirs`, but does not raise an exception if the
        directory is not empty or does not exist."""
        with contextlib.suppress(FileExistsError, DirectoryNotEmpty):
            with DirectoryNotEmpty.translate():
                self.removedirs()
        return self

    # --- Modifying operations on files

    def touch(self) -> Self:
        """Set the access/modified times of this file to the current time.
        Create the file if it does not exist.
        """
        os.close(os.open(self, os.O_WRONLY | os.O_CREAT, 0o666))
        os.utime(self, None)
        return self

    def remove(self) -> Self:
        """.. seealso:: :func:`os.remove`"""
        os.remove(self)
        return self

    def remove_p(self) -> Self:
        """Like :meth:`remove`, but does not raise an exception if the
        file does not exist."""
        with contextlib.suppress(FileNotFoundError):
            self.unlink()
        return self

    unlink = remove
    unlink_p = remove_p

    # --- Links

    def hardlink_to(self, target: str) -> None:
        """
        Create a hard link at self, pointing to target.

        .. seealso:: :func:`os.link`
        """
        os.link(target, self)

    def link(self, newpath: str) -> Self:
        """Create a hard link at `newpath`, pointing to this file.

        .. seealso:: :func:`os.link`
        """
        os.link(self, newpath)
        return self._next_class(newpath)

    def symlink_to(self, target: str, target_is_directory: bool = False) -> None:
        """
        Create a symbolic link at self, pointing to target.

        .. seealso:: :func:`os.symlink`
        """
        os.symlink(target, self, target_is_directory)

    def symlink(self, newlink: str | None = None) -> Self:
        """Create a symbolic link at `newlink`, pointing here.

        If newlink is not supplied, the symbolic link will assume
        the name self.basename(), creating the link in the cwd.

        .. seealso:: :func:`os.symlink`
        """
        if newlink is None:
            newlink = self.basename()
        os.symlink(self, newlink)
        return self._next_class(newlink)

    def readlink(self) -> Self:
        """Return the path to which this symbolic link points.

        The result may be an absolute or a relative path.

        .. seealso:: :meth:`readlinkabs`, :func:`os.readlink`
        """
        return self._next_class(removeprefix(os.readlink(self), '\\\\?\\'))

    def readlinkabs(self) -> Self:
        """Return the path to which this symbolic link points.

        The result is always an absolute path.

        .. seealso:: :meth:`readlink`, :func:`os.readlink`
        """
        p = self.readlink()
        return p if p.isabs() else (self.parent / p).absolute()

    # High-level functions from shutil.

    def copyfile(self, dst: str, *, follow_symlinks: bool = True) -> Self:
        return self._next_class(
            shutil.copyfile(self, dst, follow_symlinks=follow_symlinks)
        )

    def copymode(self, dst: str, *, follow_symlinks: bool = True) -> None:
        shutil.copymode(self, dst, follow_symlinks=follow_symlinks)

    def copystat(self, dst: str, *, follow_symlinks: bool = True) -> None:
        shutil.copystat(self, dst, follow_symlinks=follow_symlinks)

    def copy(self, dst: str, *, follow_symlinks: bool = True) -> Self:
        return self._next_class(shutil.copy(self, dst, follow_symlinks=follow_symlinks))

    def copy2(self, dst: str, *, follow_symlinks: bool = True) -> Self:
        return self._next_class(
            shutil.copy2(self, dst, follow_symlinks=follow_symlinks)
        )

    def copytree(
        self,
        dst: str,
        symlinks: bool = False,
        ignore: _IgnoreFn | None = None,
        copy_function: _CopyFn = shutil.copy2,
        ignore_dangling_symlinks: bool = False,
        dirs_exist_ok: bool = False,
    ) -> Self:
        return self._next_class(
            shutil.copytree(
                self,
                dst,
                symlinks=symlinks,
                ignore=ignore,
                copy_function=copy_function,
                ignore_dangling_symlinks=ignore_dangling_symlinks,
                dirs_exist_ok=dirs_exist_ok,
            )
        )

    def move(self, dst: str, copy_function: _CopyFn = shutil.copy2) -> Self:
        retval = shutil.move(self, dst, copy_function=copy_function)
        # shutil.move may return None if the src and dst are the same
        return self._next_class(retval or dst)

    if sys.version_info >= (3, 12):

        @overload
        def rmtree(
            self,
            ignore_errors: bool,
            onerror: _OnErrorCallback,
            *,
            onexc: None = ...,
            dir_fd: int | None = ...,
        ) -> None: ...
        @overload
        def rmtree(
            self,
            ignore_errors: bool = ...,
            *,
            onerror: _OnErrorCallback,
            onexc: None = ...,
            dir_fd: int | None = ...,
        ) -> None: ...
        @overload
        def rmtree(
            self,
            ignore_errors: bool = ...,
            *,
            onexc: _OnExcCallback | None = ...,
            dir_fd: int | None = ...,
        ) -> None: ...

    elif sys.version_info >= (3, 11):
        # NOTE: Strictly speaking, an overload is not needed - this could
        #       be expressed in a single annotation. However, if overloads
        #       are used there must be a minimum of two, so this was split
        #       into two so that the body of rmtree need not be re-defined
        #       for each version.
        @overload
        def rmtree(
            self,
            onerror: _OnErrorCallback | None = None,
            *,
            dir_fd: int | None = None,
        ) -> None: ...
        @overload
        def rmtree(
            self,
            ignore_errors: bool,
            onerror: _OnErrorCallback | None = ...,
            *,
            dir_fd: int | None = ...,
        ) -> None: ...

    else:
        # NOTE: See note about overloads above.
        @overload
        def rmtree(self, onerror: _OnErrorCallback | None = ...) -> None: ...
        @overload
        def rmtree(
            self, ignore_errors: bool, onerror: _OnErrorCallback | None = ...
        ) -> None: ...

    def rmtree(self, *args, **kwargs):
        shutil.rmtree(self, *args, **kwargs)

    # Copy the docstrings from shutil to these methods.

    copyfile.__doc__ = shutil.copyfile.__doc__
    copymode.__doc__ = shutil.copymode.__doc__
    copystat.__doc__ = shutil.copystat.__doc__
    copy.__doc__ = shutil.copy.__doc__
    copy2.__doc__ = shutil.copy2.__doc__
    copytree.__doc__ = shutil.copytree.__doc__
    move.__doc__ = shutil.move.__doc__
    rmtree.__doc__ = shutil.rmtree.__doc__

    def rmtree_p(self) -> Self:
        """Like :meth:`rmtree`, but does not raise an exception if the
        directory does not exist."""
        with contextlib.suppress(FileNotFoundError):
            self.rmtree()
        return self

    def chdir(self) -> None:
        """.. seealso:: :func:`os.chdir`"""
        os.chdir(self)

    cd = chdir

    def merge_tree(
        self,
        dst: str,
        symlinks: bool = False,
        *,
        copy_function: _CopyFn = shutil.copy2,
        ignore: _IgnoreFn = lambda dir, contents: [],
    ):
        """
        Copy entire contents of self to dst, overwriting existing
        contents in dst with those in self.

        Pass ``symlinks=True`` to copy symbolic links as links.

        Accepts a ``copy_function``, similar to copytree.

        To avoid overwriting newer files, supply a copy function
        wrapped in ``only_newer``. For example::

            src.merge_tree(dst, copy_function=only_newer(shutil.copy2))
        """
        dst_path = self._next_class(dst)
        dst_path.makedirs_p()

        sources = list(self.iterdir())
        _ignored = set(ignore(self, [item.name for item in sources]))

        def ignored(item: Self) -> bool:
            return item.name in _ignored

        for source in itertools.filterfalse(ignored, sources):
            dest = dst_path / source.name
            if symlinks and source.islink():
                target = source.readlink()
                target.symlink(dest)
            elif source.is_dir():
                source.merge_tree(
                    dest,
                    symlinks=symlinks,
                    copy_function=copy_function,
                    ignore=ignore,
                )
            else:
                copy_function(source, dest)

        self.copystat(dst_path)

    #
    # --- Special stuff from os

    if sys.platform != "win32":

        def chroot(self) -> None:  # pragma: nocover
            """.. seealso:: :func:`os.chroot`"""
            os.chroot(self)

    if sys.platform == "win32":
        if sys.version_info >= (3, 10):

            @overload
            def startfile(
                self,
                arguments: str = ...,
                cwd: str | None = ...,
                show_cmd: int = ...,
            ) -> Self: ...
            @overload
            def startfile(
                self,
                operation: str,
                arguments: str = ...,
                cwd: str | None = ...,
                show_cmd: int = ...,
            ) -> Self: ...

        else:

            @overload
            def startfile(self) -> Self: ...
            @overload
            def startfile(self, operation: str) -> Self: ...

        def startfile(self, *args, **kwargs) -> Self:  # pragma: nocover
            """.. seealso:: :func:`os.startfile`"""
            os.startfile(self, *args, **kwargs)
            return self

    # in-place re-writing, courtesy of Martijn Pieters
    # http://www.zopatista.com/python/2013/11/26/inplace-file-rewriting/
    @contextlib.contextmanager
    def in_place(
        self,
        mode: str = 'r',
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        backup_extension: str | None = None,
    ) -> Iterator[tuple[IO[Any], IO[Any]]]:
        """
        A context in which a file may be re-written in-place with
        new content.

        Yields a tuple of :samp:`({readable}, {writable})` file
        objects, where `writable` replaces `readable`.

        If an exception occurs, the old file is restored, removing the
        written data.

        Mode *must not* use ``'w'``, ``'a'``, or ``'+'``; only
        read-only-modes are allowed. A :exc:`ValueError` is raised
        on invalid modes.

        For example, to add line numbers to a file::

            p = Path(filename)
            assert p.is_file()
            with p.in_place() as (reader, writer):
                for number, line in enumerate(reader, 1):
                    writer.write('{0:3}: '.format(number)))
                    writer.write(line)

        Thereafter, the file at `filename` will have line numbers in it.
        """
        if set(mode).intersection('wa+'):
            raise ValueError('Only read-only file modes can be used')

        # move existing file to backup, create new file with same permissions
        # borrowed extensively from the fileinput module
        backup_fn = self + (backup_extension or os.extsep + 'bak')
        backup_fn.remove_p()
        self.rename(backup_fn)
        readable = open(
            backup_fn,
            mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )

        perm = os.stat(readable.fileno()).st_mode
        os_mode = os.O_CREAT | os.O_WRONLY | os.O_TRUNC
        os_mode |= getattr(os, 'O_BINARY', 0)
        fd = os.open(self, os_mode, perm)
        writable = open(
            fd,
            "w" + mode.replace('r', ''),
            buffering=buffering,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )
        with contextlib.suppress(OSError, AttributeError):
            self.chmod(perm)

        try:
            yield readable, writable
        except Exception:
            # move backup back
            readable.close()
            writable.close()
            self.remove_p()
            backup_fn.rename(self)
            raise
        else:
            readable.close()
            writable.close()
        finally:
            backup_fn.remove_p()

    @classes.ClassProperty
    @classmethod
    def special(cls) -> Callable[[str | None], SpecialResolver]:
        """
        Return a SpecialResolver object suitable referencing a suitable
        directory for the relevant platform for the given
        type of content.

        For example, to get a user config directory, invoke:

            dir = Path.special().user.config

        Uses the `appdirs
        <https://pypi.python.org/pypi/appdirs/1.4.0>`_ to resolve
        the paths in a platform-friendly way.

        To create a config directory for 'My App', consider:

            dir = Path.special("My App").user.config.makedirs_p()

        If the ``appdirs`` module is not installed, invocation
        of special will raise an ImportError.
        """
        return functools.partial(SpecialResolver, cls)


class DirectoryNotEmpty(OSError):
    @staticmethod
    @contextlib.contextmanager
    def translate() -> Iterator[None]:
        try:
            yield
        except OSError as exc:
            if exc.errno == errno.ENOTEMPTY:
                raise DirectoryNotEmpty(*exc.args) from exc
            raise


def only_newer(copy_func: _CopyFn) -> _CopyFn:
    """
    Wrap a copy function (like shutil.copy2) to return
    the dst if it's newer than the source.
    """

    @functools.wraps(copy_func)
    def wrapper(src: str, dst: str):
        src_p = Path(src)
        dst_p = Path(dst)
        is_newer_dst = dst_p.exists() and dst_p.getmtime() >= src_p.getmtime()
        if is_newer_dst:
            return dst
        return copy_func(src, dst)

    return wrapper


class ExtantPath(Path):
    """
    >>> ExtantPath('.')
    ExtantPath('.')
    >>> ExtantPath('does-not-exist')
    Traceback (most recent call last):
    OSError: does-not-exist does not exist.
    """

    def _validate(self) -> None:
        if not self.exists():
            raise OSError(f"{self} does not exist.")


class ExtantFile(Path):
    """
    >>> ExtantFile('.')
    Traceback (most recent call last):
    FileNotFoundError: . does not exist as a file.
    >>> ExtantFile('does-not-exist')
    Traceback (most recent call last):
    FileNotFoundError: does-not-exist does not exist as a file.
    """

    def _validate(self) -> None:
        if not self.is_file():
            raise FileNotFoundError(f"{self} does not exist as a file.")


class SpecialResolver:
    path_class: type
    wrapper: ModuleType

    class ResolverScope:
        paths: SpecialResolver
        scope: str

        def __init__(self, paths: SpecialResolver, scope: str) -> None:
            self.paths = paths
            self.scope = scope

        def __getattr__(self, class_: str) -> _MultiPathType:
            return self.paths.get_dir(self.scope, class_)

    def __init__(
        self,
        path_class: type,
        appname: str | None = None,
        appauthor: str | None = None,
        version: str | None = None,
        roaming: bool = False,
        multipath: bool = False,
    ):
        appdirs = importlib.import_module('appdirs')
        self.path_class = path_class
        self.wrapper = appdirs.AppDirs(
            appname=appname,
            appauthor=appauthor,
            version=version,
            roaming=roaming,
            multipath=multipath,
        )

    def __getattr__(self, scope: str) -> ResolverScope:
        return self.ResolverScope(self, scope)

    def get_dir(self, scope: str, class_: str) -> _MultiPathType:
        """
        Return the callable function from appdirs, but with the
        result wrapped in self.path_class
        """
        prop_name = f'{scope}_{class_}_dir'
        value = getattr(self.wrapper, prop_name)
        MultiPath = Multi.for_class(self.path_class)
        return MultiPath.detect(value)


class Multi:
    """
    A mix-in for a Path which may contain multiple Path separated by pathsep.
    """

    @classmethod
    def for_class(cls, path_cls: type) -> type[_MultiPathType]:
        name = 'Multi' + path_cls.__name__
        return type(name, (cls, path_cls), {})

    @classmethod
    def detect(cls, input: str) -> _MultiPathType:
        if os.pathsep not in input:
            cls = cls._next_class
        return cls(input)  # type: ignore[return-value, call-arg]

    def __iter__(self) -> Iterator[Path]:
        return iter(map(self._next_class, self.split(os.pathsep)))  # type: ignore[attr-defined]

    @classes.ClassProperty
    @classmethod
    def _next_class(cls) -> type[Path]:
        """
        Multi-subclasses should use the parent class
        """
        return next(class_ for class_ in cls.__mro__ if not issubclass(class_, Multi))  # type: ignore[return-value]


class _MultiPathType(Multi, Path):
    pass


class TempDir(Path):
    """
    A temporary directory via :func:`tempfile.mkdtemp`, and
    constructed with the same parameters that you can use
    as a context manager.

    For example:

    >>> with TempDir() as d:
    ...     d.is_dir() and isinstance(d, Path)
    True

    The directory is deleted automatically.

    >>> d.is_dir()
    False

    .. seealso:: :func:`tempfile.mkdtemp`
    """

    @classes.ClassProperty
    @classmethod
    def _next_class(cls) -> type[Path]:
        return Path

    def __new__(cls, *args, **kwargs) -> Self:
        dirname = tempfile.mkdtemp(*args, **kwargs)
        return super().__new__(cls, dirname)

    def __init__(self) -> None:
        pass

    def __enter__(self) -> Self:
        # TempDir should return a Path version of itself and not itself
        # so that a second context manager does not create a second
        # temporary directory, but rather changes CWD to the location
        # of the temporary directory.
        return self._next_class(self)

    def __exit__(self, *_) -> None:
        self.rmtree()


class Handlers:
    @staticmethod
    def strict(msg: str) -> Never:
        raise

    @staticmethod
    def warn(msg: str) -> None:
        warnings.warn(msg, TreeWalkWarning, stacklevel=2)

    @staticmethod
    def ignore(msg: str) -> None:
        pass

    @classmethod
    def _resolve(cls, param: str | Callable[[str], None]) -> Callable[[str], None]:
        msg = "invalid errors parameter"
        if isinstance(param, str):
            if param not in vars(cls):
                raise ValueError(msg)
            return {"strict": cls.strict, "warn": cls.warn, "ignore": cls.ignore}[param]
        else:
            if not callable(param):
                raise ValueError(msg)
            return param
