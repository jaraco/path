#!/usr/bin/env python

from __future__ import with_statement

try:
    import setuptools as impl
except ImportError:
    import distutils.core as impl

from distutils.command.build_py import build_py

with open('README.rst') as ld_file:
    long_description = ld_file.read()

kw = dict(
    name = "path.py",
    version = "4.0",
    description = "A module wrapper for os.path",
    long_description = long_description,
    author = "Jason Orendorff",
    author_email = "jason.orendorff@gmail.com",
    maintainer = "Jason R. Coombs",
    maintainer_email = "jaraco@jaraco.com",
    url = "http://github.com/jaraco/path.py",
    license = "MIT License",
    py_modules = ['path', 'test_path'],
    cmdclass = dict(build_py=build_py),
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)


if __name__ == '__main__':
    impl.setup(**kw)
