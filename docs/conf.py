#!/usr/bin/env python3
# -*- coding: utf-8 -*-

extensions = [
    "sphinx.ext.autodoc",
    "jaraco.packaging.sphinx",
    "rst.linker",
    "sphinx.ext.intersphinx",
]

pygments_style = "sphinx"

intersphinx_mapping = {'python': ('http://docs.python.org/', None)}

link_files = {
    '../CHANGES.rst': dict(
        using=dict(GH='https://github.com'),
        replace=[
            dict(
                pattern=r'(Issue #|\B#)(?P<issue>\d+)',
                url='{package_url}/issues/{issue}',
            ),
            dict(
                pattern=r'(?m:^((?P<scm_version>v?\d+(\.\d+){1,2}))\n[-=]+\n)',
                with_scm='{text}\n{rev[timestamp]:%d %b %Y}\n',
            ),
            dict(
                pattern=r'PEP[- ](?P<pep_number>\d+)',
                url='https://www.python.org/dev/peps/pep-{pep_number:0>4}/',
            ),
        ],
    )
}

# Be strict about any broken references:
nitpicky = True

# Custom sidebar templates, maps document names to template names.
html_theme = 'alabaster'
templates_path = ['_templates']
html_sidebars = {'index': ['tidelift-sidebar.html']}
