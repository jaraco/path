# encoding: utf-8

project = 'path.py'
copyright = '2013, Mikhail Gusarov, Jason R. Coombs'

import path
import re

release = path.__version__
version = re.match('[^.]+[.][^.]+', release).group(0)

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
	'CHANGES.rst': dict(
		using=dict(
			GH='https://github.com',
		),
		replace=[
			dict(
				pattern=r"(Issue )?#(?P<issue>\d+)",
				url='{GH}/jaraco/path.py/issues/{issue}',
			),
			dict(
				pattern=r"Pull Request ?#(?P<pull_request>\d+)",
				url='{GH}/jaraco/path.py/pull/{pull_request}',
			),
		],
	),
}
