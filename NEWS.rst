v17.1.0
=======

Features
--------

- Fully inlined the type annotations. Big thanks to SethMMorton. (#235)


v17.0.0
=======

Deprecations and Removals
-------------------------

- Removed deprecated methods ``getcwd``, ``abspath``, ``ext``, ``listdir``, ``isdir``, ``isfile``, and ``text``.
- Removed deprecated support for passing ``bytes`` to ``write_text`` and ``write_lines(linesep=)`` parameter.


v16.16.0
========

Features
--------

- Implement .replace. (#214)
- Add .home classmethod. (#214)


v16.15.0
========

Features
--------

- Replaced 'open' overloads with 'functools.wraps(open)' for simple re-use. (#225)


Bugfixes
--------

- Add type hints for .with_name, .suffix, .with_stem. (#227)
- Add type hint for .absolute. (#228)


v16.14.0
========

Features
--------

- Add .symlink_to and .hardlink_to. (#214)
- Add .cwd method and deprecated .getcwd. (#214)


v16.13.0
========

Features
--------

- Create 'absolute' method and deprecate 'abspath'. (#214)
- In readlink, prefer the display path to the substitute path. (#222)


v16.12.1
========

Bugfixes
--------

- Restore functionality in .isdir and .isfile.


v16.12.0
========

Features
--------

- Added .is_dir and .is_file for parity with pathlib. Deprecates .isdir and .isfile. (#214)


v16.11.0
========

Features
--------

- Inlined some types. (#215)


v16.10.2
========

Bugfixes
--------

- Fix iterdir - it also accepts match. Ref #220. (#220)


v16.10.1
========

Bugfixes
--------

- Add type annotation for iterdir. (#220)


v16.10.0
========

Features
--------

- Added .with_name and .with_stem.
- Prefer .suffix to .ext and deprecate .ext.


v16.9.0
=======

Features
--------

- Added ``.iterdir()`` and deprecated ``.listdir()``. (#214)


v16.8.0
=======

Features
--------

- Use '.' as the default path. (#216)


v16.7.1
=======

Bugfixes
--------

- Set ``stacklevel=2`` in deprecation warning for ``.text``. (#210)


v16.7.0
=======

Features
--------

- Added ``.permissions`` attribute. (#211)
- Require Python 3.8 or later.


v16.6.0
-------

- ``.mtime`` and ``.atime`` are now settable.

v16.5.0
-------

- Refreshed packaging.
- #197: Fixed default argument rendering in docs.
- #209: Refactored ``write_lines`` to re-use open semantics.
  Deprecated the ``linesep`` parameter.

v16.4.0
-------

- #207: Added type hints and declare the library as typed.

v16.3.0
-------

- Require Python 3.7 or later.
- #205: test_listdir_other_encoding now automatically skips
  itself on file systems where it's not appropriate.

v16.2.0
-------

- Deprecated passing bytes to ``write_text``. Instead, users
  should call ``write_bytes``.

v16.1.0
-------

- #204: Improved test coverage across the package to 99%, fixing
  bugs in uncovered code along the way.

v16.0.0
-------

- #200: ``TempDir`` context now cleans up unconditionally,
  even if an exception occurs.

v15.1.2
-------

- #199: Fixed broken link in README.

v15.1.1
-------

- Refreshed package metadata.

v15.1.0
-------

- Added ``ExtantPath`` and ``ExtantFile`` objects that raise
  errors when they reference a non-existent path or file.

v15.0.1
-------

- Refreshed package metadata.

v15.0.0
-------

- Removed ``__version__`` property. To determine the version,
  use ``importlib.metadata.version('path')``.

v14.0.1
-------

- Fixed regression on Python 3.7 and earlier where ``lru_cache``
  did not support a user function.

v14.0.0
-------

- Removed ``namebase`` property. Use ``stem`` instead.
- Removed ``update`` parameter on method to
  ``Path.merge_tree``. Instead, to only copy newer files,
  provide a wrapped ``copy`` function, as described in the
  doc string.
- Removed ``FastPath``. Just use ``Path``.
- Removed ``path.CaseInsensitivePattern``. Instead
  use ``path.matchers.CaseInsensitive``.
- Removed ``path.tempdir``. Use ``path.TempDir``.
- #154: Added ``Traversal`` class and support for customizing
  the behavior of a ``Path.walk``.

v13.3.0
-------

- #186: Fix test failures on Python 3.8 on Windows by relying on
  ``realpath()`` instead of ``readlink()``.
- #189: ``realpath()`` now honors symlinks on Python 3.7 and
  earlier, approximating the behavior found on Python 3.8.
- #187: ``lines()`` no longer relies on the deprecated ``.text()``.

v13.2.0
-------

- Require Python 3.6 or later.

v13.1.0
-------

- #170: Added ``read_text`` and ``read_bytes`` methods to
  align with ``pathlib`` behavior. Deprecated ``text`` method.
  If you require newline normalization of ``text``, use
  ``jaraco.text.normalize_newlines(Path.read_text())``.

v13.0.0
-------

- #169: Renamed package from ``path.py`` to ``path``. The docs
  make reference to a pet name "path pie" for easier discovery.

v12.5.0
-------

- #195: Project now depends on ``path``.

v12.4.0
-------

- #169: Project now depends on ``path < 13.2``.
- Fixed typo in README.

v12.3.0
-------

- #169: Project is renamed to simply ``path``. This release of
  ``path.py`` simply depends on ``path < 13.1``.

v12.2.0
-------

- #169: Moved project at GitHub from ``jaraco/path.py`` to
  ``jaraco/path``.

v12.1.0
-------

- #171: Fixed exception in ``rmdir_p`` when target is not empty.
- #174: Rely on ``importlib.metadata`` on Python 3.8.

v12.0.2
-------

- Refreshed package metadata.

12.0.1
------

- #166: Removed 'universal' wheel support.

12.0
---

- #148: Dropped support for Python 2.7 and 3.4.
- Moved 'path' into a package.

11.5.2
------

- #163: Corrected 'pymodules' typo in package declaration.

11.5.1
------

- Minor packaging refresh.

11.5.0
------

- #156: Re-wrote the handling of pattern matches for
  ``listdir``, ``walk``, and related methods, allowing
  the pattern to be a more complex object. This approach
  drastically simplifies the code and obviates the
  ``CaseInsensitivePattern`` and ``FastPath`` classes.
  Now the main ``Path`` class should be as performant
  as ``FastPath`` and case-insensitive matches can be
  readily constructed using the new
  ``path.matchers.CaseInsensitive`` class.

11.4.1
------

- #153: Skip intermittently failing performance test on
  Python 2.

11.4.0
------

- #130: Path.py now supports non-decodable filenames on
  Linux and Python 2, leveraging the
  `backports.os <https://pypi.org/project/backports.os>`_
  package (as an optional dependency). Currently, only
  ``listdir`` is patched, but other ``os`` primitives may
  be patched similarly in the ``patch_for_linux_python2``
  function.

- #141: For merge_tree, instead of relying on the deprecated
  distutils module, implement merge_tree explicitly. The
  ``update`` parameter is deprecated, instead superseded
  by a ``copy_function`` parameter and an ``only_newer``
  wrapper for any copy function.

11.3.0
------

- #151: No longer use two techniques for splitting lines.
  Instead, unconditionally rely on io.open for universal
  newlines support and always use splitlines.

11.2.0
------

- #146: Rely on `importlib_metadata
  <https://pypi.org/project/importlib_metadata>`_ instead of
  setuptools/pkg_resources to load the version of the module.
  Added tests ensuring a <100ms import time for the ``path``
  module. This change adds an explicit dependency on the
  importlib_metadata package, but the project still supports
  copying of the ``path.py`` module without any dependencies.

11.1.0
------

- #143, #144: Add iglob method.
- #142, #145: Rename ``tempdir`` to ``TempDir`` and declare
  it as part of ``__all__``. Retain ``tempdir`` for compatibility
  for now.
- #145: ``TempDir.__enter__`` no longer returns the ``TempDir``
  instance, but instead returns a ``Path`` instance, suitable for
  entering to change the current working directory.

11.0.1
------

- #136: Fixed test failures on BSD.

- Refreshed package metadata.

11.0
----

- Drop support for Python 3.3.

10.6
----

- Renamed ``namebase`` to ``stem`` to match API of pathlib.
  Kept ``namebase`` as a deprecated alias for compatibility.

- Added new ``with_suffix`` method, useful for renaming the
  extension on a Path::

    orig = Path('mydir/mypath.bat')
    renamed = orig.rename(orig.with_suffix('.cmd'))

10.5
----

- Packaging refresh and readme updates.

10.4
----

- #130: Removed surrogate_escape handler as it's no longer
  used.

10.3.1
------

- #124: Fixed ``rmdir_p`` raising ``FileNotFoundError`` when
  directory does not exist on Windows.

10.3
----

- #115: Added a new performance-optimized implementation
  for listdir operations, optimizing ``listdir``, ``walk``,
  ``walkfiles``, ``walkdirs``, and ``fnmatch``, presented
  as the ``FastPath`` class.

  Please direct feedback on this implementation to the ticket,
  especially if the performance benefits justify it replacing
  the default ``Path`` class.

10.2
----

- Symlink no longer requires the ``newlink`` parameter
  and will default to the basename of the target in the
  current working directory.

10.1
----

- #123: Implement ``Path.__fspath__`` per PEP 519.

10.0
----

- Once again as in 8.0 remove deprecated ``path.path``.

9.1
---

- #121: Removed workaround for #61 added in 5.2. ``path.py``
  now only supports file system paths that can be effectively
  decoded to text. It is the responsibility of the system
  implementer to ensure that filenames on the system are
  decodeable by ``sys.getfilesystemencoding()``.

9.0
---

- Drop support for Python 2.6 and 3.2 as integration
  dependencies (pip) no longer support these versions.

8.3
---

- Merge with latest skeleton, adding badges and test runs by
  default under tox instead of pytest-runner.
- Documentation is no longer hosted with PyPI.

8.2.1
-----

- #112: Update Travis CI usage to only deploy on Python 3.5.

8.2
---

- Refreshed project metadata based on `jaraco's project
  skeleton <https://github.com/jaraco/skeleton/tree/spaces>`_.

- Releases are now automatically published via Travis-CI.
- #111: More aggressively trap errors when importing
  ``pkg_resources``.

8.1.2
-----

- #105: By using unicode literals, avoid errors rendering the
  backslash in __get_owner_windows.

8.1.1
-----

- #102: Reluctantly restored reference to path.path in ``__all__``.

8.1
---

- #102: Restored ``path.path`` with a DeprecationWarning.

8.0
---

Removed ``path.path``. Clients must now refer to the canonical
name, ``path.Path`` as introduced in 6.2.

7.7
---

- #88: Added support for resolving certain directories on a
  system to platform-friendly locations using the `appdirs
  <https://pypi.python.org/pypi/appdirs/1.4.0>`_ library. The
  ``Path.special`` method returns an ``SpecialResolver`` instance
  that will resolve a path in a scope
  (i.e. 'site' or 'user') and class (i.e. 'config', 'cache',
  'data'). For
  example, to create a config directory for "My App"::

      config_dir = Path.special("My App").user.config.makedirs_p()

  ``config_dir`` will exist in a user context and will be in a
  suitable platform-friendly location.

  As ``path.py`` does not currently have any dependencies, and
  to retain that expectation for a compatible upgrade path,
  ``appdirs`` must be installed to avoid an ImportError when
  invoking ``special``.


- #88: In order to support "multipath" results, where multiple
  paths are returned in a single, ``os.pathsep``-separated
  string, a new class MultiPath now represents those special
  results. This functionality is experimental and may change.
  Feedback is invited.

7.6.2
-----

- Re-release of 7.6.1 without unintended feature.

7.6.1
-----

- #101: Supress error when `path.py` is not present as a distribution.

7.6
---

- #100: Add ``merge_tree`` method for merging
  two existing directory trees.
- Uses `setuptools_scm <https://github.org/pypa/setuptools_scm>`_
  for version management.

7.5
---

- #97: ``__rdiv__`` and ``__rtruediv__`` are now defined.

7.4
---

- #93: chown now appears in docs and raises NotImplementedError if
  ``os.chown`` isn't present.
- #92: Added compatibility support for ``.samefile`` on platforms without
  ``os.samefile``.

7.3
---

 - #91: Releases now include a universal wheel.

7.2
---

 - In chmod, added support for multiple symbolic masks (separated by commas).
 - In chmod, fixed issue in setting of symbolic mask with '=' where
   unreferenced permissions were cleared.

7.1
---

 - #23: Added support for symbolic masks to ``.chmod``.

7.0
---

 - The ``open`` method now uses ``io.open`` and supports all of the
   parameters to that function. ``open`` will always raise an ``OSError``
   on failure, even on Python 2.
 - Updated ``write_text`` to support additional newline patterns.
 - The ``text`` method now always returns text (never bytes), and thus
   requires an encoding parameter be supplied if the default encoding is not
   sufficient to decode the content of the file.

6.2
---

 - ``path`` class renamed to ``Path``. The ``path`` name remains as an alias
   for compatibility.

6.1
---

 - ``chown`` now accepts names in addition to numeric IDs.

6.0
---

 - Drop support for Python 2.5. Python 2.6 or later required.
 - Installation now requires setuptools.

5.3
---

 - Allow arbitrary callables to be passed to path.walk ``errors`` parameter.
   Enables workaround for issues such as #73 and #56.

5.2
---

 - #61: path.listdir now decodes filenames from os.listdir when loading
   characters from a file. On Python 3, the behavior is unchanged. On Python
   2, the behavior will now mimick that of Python 3, attempting to decode
   all filenames and paths using the encoding indicated by
   ``sys.getfilesystemencoding()``, and escaping any undecodable characters
   using the 'surrogateescape' handler.

5.1
---

 - #53: Added ``path.in_place`` for editing files in place.

5.0
---

 - ``path.fnmatch`` now takes an optional parameter ``normcase`` and this
   parameter defaults to self.module.normcase (using case normalization most
   pertinent to the path object itself). Note that this change means that
   any paths using a custom ntpath module on non-Windows systems will have
   different fnmatch behavior. Before::

       # on Unix
       >>> p = path('Foo')
       >>> p.module = ntpath
       >>> p.fnmatch('foo')
       False

   After::

       # on any OS
       >>> p = path('Foo')
       >>> p.module = ntpath
       >>> p.fnmatch('foo')
       True

   To maintain the original behavior, either don't define the 'module' for the
   path or supply explicit normcase function::

       >>> p.fnmatch('foo', normcase=os.path.normcase)
       # result always varies based on OS, same as fnmatch.fnmatch

   For most use-cases, the default behavior should remain the same.

 - Issue #50: Methods that accept patterns (``listdir``, ``files``, ``dirs``,
   ``walk``, ``walkdirs``, ``walkfiles``, and ``fnmatch``) will now use a
   ``normcase`` attribute if it is present on the ``pattern`` parameter. The
   path module now provides a ``CaseInsensitivePattern`` wrapper for strings
   suitable for creating case-insensitive patterns for those methods.

4.4
---

 - Issue #44: _hash method would open files in text mode, producing
   invalid results on Windows. Now files are opened in binary mode, producing
   consistent results.
 - Issue #47: Documentation is dramatically improved with Intersphinx links
   to the Python os.path functions and documentation for all methods and
   properties.

4.3
---

 - Issue #32: Add ``chdir`` and ``cd`` methods.

4.2
---

 - ``open()`` now passes all positional and keyword arguments through to the
   underlying ``builtins.open`` call.

4.1
---

 - Native Python 2 and Python 3 support without using 2to3 during the build
   process.

4.0
---

 - Added a ``chunks()`` method to a allow quick iteration over pieces of a
   file at a given path.
 - Issue #28: Fix missing argument to ``samefile``.
 - Initializer no longer enforces `isinstance basestring` for the source
   object. Now any object that supplies ``__unicode__`` can be used by a
   ``path`` (except None). Clients that depend on a ValueError being raised
   for ``int`` and other non-string objects should trap these types
   internally.
 - Issue #30: ``chown`` no longer requires both uid and gid to be provided
   and will not mutate the ownership if nothing is provided.

3.2
---

 - Issue #22: ``__enter__`` now returns self.

3.1
---

 - Issue #20: `relpath` now supports a "start" parameter to match the
   signature of `os.path.relpath`.

3.0
---

 - Minimum Python version is now 2.5.

2.6
---

 - Issue #5: Implemented `path.tempdir`, which returns a path object which is
   a temporary directory and context manager for cleaning up the directory.
 - Issue #12: One can now construct path objects from a list of strings by
   simply using path.joinpath. For example::

     path.joinpath('a', 'b', 'c') # or
     path.joinpath(*path_elements)

2.5
---

 - Issue #7: Add the ability to do chaining of operations that formerly only
   returned None.
 - Issue #4: Raise a TypeError when constructed from None.
