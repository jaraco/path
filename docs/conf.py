#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pkg_resources

extensions = [
    'sphinx.ext.autodoc',
    'rst.linker',
]

# General information about the project.
project = 'path.py'
copyright = '2013-2016 Mikhail Gusarov, Jason R. Coombs'

# The short X.Y version.
version = pkg_resources.require(project)[0].version
# The full version, including alpha/beta/rc tags.
release = version

pygments_style = 'sphinx'
html_theme = 'alabaster'
html_static_path = ['_static']
htmlhelp_basename = 'pathpydoc'
templates_path = ['_templates']
exclude_patterns = ['_build']
source_suffix = '.rst'
master_doc = 'index'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'rst.linker']

intersphinx_mapping = {'python': ('http://docs.python.org/', None)}

link_files = {
	'../CHANGES.rst': dict(
		using=dict(
			GH='https://github.com',
			project=project,
		),
		replace=[
			dict(
				pattern=r"(Issue )?#(?P<issue>\d+)",
				url='{GH}/jaraco/{project}/issues/{issue}',
			),
			dict(
				pattern=r"Pull Request ?#(?P<pull_request>\d+)",
				url='{GH}/jaraco/{project}/pull/{pull_request}',
			),
			dict(
				pattern=r"^(?m)((?P<scm_version>v?\d+(\.\d+){1,2}))\n[-=]+\n",
				with_scm="{text}\n{rev[timestamp]:%d %b %Y}\n",
			),
		],
	),
}
