#!/usr/bin/env python

import distutils.core

# Setup script for path

kw = {
    'name': "path.py",
    'version': "2.2.2",
    'description': "A module wrapper for os.path",
    'author': "Mikhail Gusarov",
    'author_email': "dottedmag@dottedmag.net",
    'url': "http://github.com/dottedmag/path.py",
    'license': "Public domain",
    'py_modules': ['path', 'test_path']
    }


# If we're running Python 2.3, add extra information
if hasattr(distutils.core, 'setup_keywords'):
    if 'classifiers' in distutils.core.setup_keywords:
        kw['classifiers'] = [
            'Development Status :: 5 - Production/Stable',
            'License :: Freely Distributable',
            'Intended Audience :: Developers',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules'
          ]
    if 'download_url' in distutils.core.setup_keywords:
        urlfmt = "http://github.com/dottedmag/celery/tarball/%s"
        kw['download_url'] = urlfmt % kw['version']


distutils.core.setup(**kw)
