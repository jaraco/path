#!/usr/bin/env python

# Project skeleton maintained at https://github.com/jaraco/skeleton

import io

import setuptools

with io.open('README.rst', encoding='utf-8') as readme:
    long_description = readme.read()

name = 'path.py'
description = 'A module wrapper for os.path'

params = dict(
    name=name,
    use_scm_version=True,
    author="Jason Orendorff",
    author_email="jason.orendorff@gmail.com",
    maintainer="Jason R. Coombs",
    maintainer_email="jaraco@jaraco.com",
    description=description or name,
    long_description=long_description,
    url="https://github.com/jaraco/" + name,
    py_modules=['path', 'test_path'],
    install_requires=[
    ],
    extras_require={
    },
    setup_requires=[
        'setuptools_scm>=1.15.0',
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
    },
)
if __name__ == '__main__':
	setuptools.setup(**params)
