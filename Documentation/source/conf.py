import os
import sys

# Point autodoc at the pyntacle source tree
sys.path.insert(0, os.path.abspath('../../pyntacle'))
os.environ.setdefault('PYNTACLE_DOCS', '1')

project = 'Pyntacle'
copyright = '2024, Tommaso Mazza, Alessandro Napoli, Manuel Mangoni, Michele Pieroni'
author = 'Tommaso Mazza, Alessandro Napoli, Manuel Mangoni, Michele Pieroni'
release = '1.3.3'

extensions = [
    "sphinx_design",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
]

autosectionlabel_prefix_document = True

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True

autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}

templates_path = ['_templates']

exclude_patterns = [
    "_parts/**",
    "**/_parts/**",
    "cli.bak_*",
    "**/cli.bak_*/**",
]

master_doc = "index"

html_theme = "sphinx_rtd_theme"

html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 3,
    "titles_only": False,
    "logo_only": False,
}
html_logo = "_static/pyntacle_new.png"

source_suffix = {'.rst': 'restructuredtext'}
