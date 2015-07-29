#!/usr/bin/env python

import re
import sys

import setuptools

with open('README.rst') as ld_file:
    long_description = ld_file.read()

with open('CHANGES.rst') as ld_file:
    long_description += '\n\n' + ld_file.read()

# match the version indicated in path.py
with open('path.py') as path_mod:
    source = path_mod.read()
    pattern = re.compile(r'''__version__ = ['"](?P<version>[\d.]+)['"]''')
    version = pattern.search(source).group('version')

needs_sphinx = set(['build_sphinx', 'upload_docs']).intersection(sys.argv)
sphinx_req = ['sphinx'] if needs_sphinx else []
needs_pytest = set(['pytest', 'test']).intersection(sys.argv)
pytest_runner = ['pytest-runner>=2.6'] if needs_pytest else []

setup_params = dict(
    name="path.py",
    version=version,
    description="A module wrapper for os.path",
    long_description=long_description,
    author="Jason Orendorff",
    author_email="jason.orendorff@gmail.com",
    maintainer="Jason R. Coombs",
    maintainer_email="jaraco@jaraco.com",
    url="http://github.com/jaraco/path.py",
    license="MIT License",
    py_modules=['path', 'test_path'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    setup_requires=sphinx_req + pytest_runner,
    tests_require=['pytest'],
    extras_require={
        ':python_version=="2.6"': ['importlib'],
    },
)


if __name__ == '__main__':
    setuptools.setup(**setup_params)
