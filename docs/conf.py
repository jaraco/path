# encoding: utf-8

project = u'path.py'
copyright = u'2013, Mikhail Gusarov, Jason R. Coombs'
version = '3.2'
release = '3.2.0'

pygments_style = 'sphinx'
html_theme = 'default'
html_static_path = ['_static']
htmlhelp_basename = 'pathpydoc'
templates_path = ['_templates']
exclude_patterns = ['_build']
source_suffix = '.rst'
master_doc = 'index'

extensions = ['sphinx.ext.autodoc']
