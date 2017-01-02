#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

extensions = [
    'sphinx.ext.autodoc',
    'rst.linker',
]

# General information about the project.

root = os.path.join(os.path.dirname(__file__), '..')
setup_script = os.path.join(root, 'setup.py')
fields = ['--name', '--version', '--url', '--author']
dist_info_cmd = [sys.executable, setup_script] + fields
output_bytes = subprocess.check_output(dist_info_cmd, cwd=root)
project, version, url, author = output_bytes.decode('utf-8').strip().split('\n')

copyright = '2010-2017 ' + author

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
			url=url,
		),
		replace=[
			dict(
				pattern=r"(Issue )?#(?P<issue>\d+)",
				url='{url}/issues/{issue}',
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
