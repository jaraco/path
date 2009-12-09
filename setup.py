#!/usr/bin/env python

import distutils.core

# Setup script for path

kw = {
    'name': "path",
    'version': "2.2",
    'description': "A module wrapper for os.path",
    'author': "Jason Orendorff",
    'author_email': "jason@jorendorff.com",
    'url': "http://www.jorendorff.com/articles/python/path/",
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
        urlfmt = "http://www.jorendorff.com/articles/python/path/path-%s.zip"
        kw['download_url'] = urlfmt % kw['version']


distutils.core.setup(**kw)
