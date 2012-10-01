#!/usr/bin/env python

import distutils.core

try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

# Setup script for path

kw = dict(
    name = "path.py",
    version = "2.4.1",
    description = "A module wrapper for os.path",
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
        'Programming Language :: Python :: 2.3',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)


distutils.core.setup(**kw)
