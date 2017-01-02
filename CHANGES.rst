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
  skeleton <https://github.com/jaraco/skeleton/tree/spaces>_.
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

- Pull Request #100: Add ``merge_tree`` method for merging
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
