Changes
=======

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
