.. image:: https://img.shields.io/pypi/v/path.svg
   :target: `PyPI link`_

.. image:: https://img.shields.io/pypi/pyversions/path.svg
   :target: `PyPI link`_

.. _PyPI link: https://pypi.org/project/path

.. image:: https://dev.azure.com/jaraco/path/_apis/build/status/jaraco.path?branchName=master
   :target: https://dev.azure.com/jaraco/path/_build/latest?definitionId=1&branchName=master

.. image:: https://img.shields.io/travis/jaraco/path/master.svg
   :target: https://travis-ci.org/jaraco/path

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: Black

.. image:: https://img.shields.io/appveyor/ci/jaraco/path/master.svg
   :target: https://ci.appveyor.com/project/jaraco/path/branch/master

.. image:: https://readthedocs.org/projects/path/badge/?version=latest
   :target: https://path.readthedocs.io/en/latest/?badge=latest

.. image:: https://tidelift.com/badges/package/pypi/path
   :target: https://tidelift.com/subscription/pkg/pypi-path?utm_source=pypi-path&utm_medium=readme


``path`` (aka path pie, formerly ``path.py``) implements path
objects as first-class entities, allowing common operations on
files to be invoked on those path objects directly. For example:

.. code-block:: python

    from path import Path

    d = Path("/home/guido/bin")
    for f in d.files("*.py"):
        f.chmod(0o755)

    # Globbing
    for f in d.files("*.py"):
        f.chmod("u+rwx")

    # Changing the working directory:
    with Path("somewhere"):
        # cwd in now `somewhere`
        ...

    # Concatenate paths with /
    foo_txt = Path("bar") / "foo.txt"

Path pie is `hosted at Github <https://github.com/jaraco/path>`_.

Find `the documentation here <https://path.readthedocs.io>`_.

Guides and Testimonials
=======================

Yasoob wrote the Python 101 `Writing a Cleanup Script
<http://freepythontips.wordpress.com/2014/01/23/python-101-writing-a-cleanup-script/>`_
based on ``path``.

Advantages
==========

Python 3.4 introduced
`pathlib <https://docs.python.org/3/library/pathlib.html>`_,
which shares many characteristics with ``path``. In particular,
it provides an object encapsulation for representing filesystem paths.
One may have imagined ``pathlib`` would supersede ``path``.

But the implementation and the usage quickly diverge, and ``path``
has several advantages over ``pathlib``:

- ``path`` implements ``Path`` objects as a subclass of
  ``str``, and as a result these ``Path``
  objects may be passed directly to other APIs that expect simple
  text representations of paths, whereas with ``pathlib``, one
  must first cast values to strings before passing them to
  APIs unaware of ``pathlib``. This shortcoming was `addressed
  by PEP 519 <https://www.python.org/dev/peps/pep-0519/>`_,
  in Python 3.6.
- ``path`` goes beyond exposing basic functionality of a path
  and exposes commonly-used behaviors on a path, providing
  methods like ``rmtree`` (from shlib) and ``remove_p`` (remove
  a file if it exists).
- As a PyPI-hosted package, ``path`` is free to iterate
  faster than a stdlib package. Contributions are welcome
  and encouraged.
- ``path`` provides a uniform abstraction over its Path object,
  freeing the implementer to subclass it readily. One cannot
  subclass a ``pathlib.Path`` to add functionality, but must
  subclass ``Path``, ``PosixPath``, and ``WindowsPath``, even
  if one only wishes to add a ``__dict__`` to the subclass
  instances.  ``path`` instead allows the ``Path.module``
  object to be overridden by subclasses, defaulting to the
  ``os.path``. Even advanced uses of ``path.Path`` that
  subclass the model do not need to be concerned with
  OS-specific nuances.

Alternatives
============

In addition to
`pathlib <https://docs.python.org/3/library/pathlib.html>`_, the
`pylib project <https://pypi.org/project/py/>`_ implements a
`LocalPath <https://github.com/pytest-dev/py/blob/72601dc8bbb5e11298bf9775bb23b0a395deb09b/py/_path/local.py#L106>`_
class, which shares some behaviors and interfaces with ``path``.

Development
===========

To install a development version, use the Github links to clone or
download a snapshot of the latest code. Alternatively, if you have git
installed, you may be able to use ``pip`` to install directly from
the repository::

    pip install git+https://github.com/jaraco/path.git

Testing
=======

Tests are invoked with `tox <https://pypi.org/project/tox>`_. After
having installed tox, simply invoke ``tox`` in a checkout of the repo
to invoke the tests.

Tests are also run in continuous integration. See the badges above
for links to the CI runs.

Releasing
=========

Tagged releases are automatically published to PyPI by Azure
Pipelines, assuming the tests pass.

Origins
=======

The ``path.py`` project was initially released in 2003 by Jason Orendorff
and has been continuously developed and supported by several maintainers
over the years.

For Enterprise
==============

Available as part of the Tidelift Subscription.

This project and the maintainers of thousands of other packages are working with Tidelift to deliver one enterprise subscription that covers all of the open source you use.

`Learn more <https://tidelift.com/subscription/pkg/pypi-PROJECT?utm_source=pypi-PROJECT&utm_medium=referral&utm_campaign=github>`_.

Security Contact
================

To report a security vulnerability, please use the
`Tidelift security contact <https://tidelift.com/security>`_.
Tidelift will coordinate the fix and disclosure.
