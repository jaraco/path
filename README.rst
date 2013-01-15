path.py
=======

`path.py` implements a path objects as first-class entities, allowing
common operations on files to be invoked on those path objects directly. For
example::

    from path import path
    d = path('/home/guido/bin')
    for f in d.files('*.py'):
        f.chmod(0755)

`path.py` is `hosted at Github <https://github.com/jaraco/path.py>`_.

Installing
==========

Path.py may be installed using setuptools or distribute or pip::

    easy_install path.py

The latest release is always updated to the `Python Package Index
<http://pypy.python.org/pypi>`_.

You may also always download the source distribution (zip/tarball), extract
it, and run `python setup.py` to install it.

Development
===========

To install an in-development version, use the Github links to clone or
download a snapshot of the latest code. Alternatively, if you have git
installed, you may be able to use pip or easy_install to install directly from
the repository::

    easy_install git+https://github.com/jaraco/path.py.git

Testing
=======

Tests are continuously run by Travis-CI: |BuildStatus|_

.. |BuildStatus| image:: https://secure.travis-ci.org/jaraco/path.py.png
.. _BuildStatus: http://travis-ci.org/jaraco/path.py

To run the tests, refer to the .travis.yml file for the steps run on the
Travis-CI hosts.
