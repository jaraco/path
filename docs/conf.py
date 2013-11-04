# encoding: utf-8

project = u'path.py'
copyright = u'2013, Mikhail Gusarov, Jason R. Coombs'

import path
import re

release = path.__version__
version = re.match('[^.]+[.][^.]+', release).group(0)

pygments_style = 'sphinx'
html_theme = 'default'
html_static_path = ['_static']
htmlhelp_basename = 'pathpydoc'
templates_path = ['_templates']
exclude_patterns = ['_build']
source_suffix = '.rst'
master_doc = 'index'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx']

intersphinx_mapping = {'python': ('http://docs.python.org/', None)}
