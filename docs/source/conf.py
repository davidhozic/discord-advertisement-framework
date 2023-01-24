# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys


sys.path.insert(0, os.path.abspath('../../src/'))
sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------
project = 'Discord Advertisement Framework'
copyright = '2022, David Hozic'
author = 'David Hozic'
version = None
gh_release = os.environ.get("GITHUB_REF_NAME", default=None) # Workflow run release
readthedocs_release = os.environ.get("READTHEDOCS_VERSION", default=None) # Readthe docs version
if gh_release is not None:
    version = gh_release
elif readthedocs_release is not None:
    version = readthedocs_release
else:
    version = "v0.0.1"


# -- General configuration ---------------------------------------------------
root_doc = 'index'

numfig = True
# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "enum_tools.autoenum",
    "sphinx_design",
    "sphinx_search.extension",
    "sphinxcontrib.inkscapeconverter"
]


source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# Autodoc
autodoc_typehints = "signature"
autodoc_typehints_format = "short"


developement_build = os.environ.get("DOC_DEVELOPMENT", default="False")
developement_build = True if developement_build == "True" else False

autodoc_default_options = {
    'member-order': 'bysource',
    "private-members": developement_build
}


# Intersphinx
intersphinx_mapping = {
    'PyCord': ("https://docs.pycord.dev/en/stable/", None),
    "Python" : ("https://docs.python.org/3/", None)
}

# ----------- HTML ----------- #
html_title = project
html_logo = "./DEP/images/logo.png"
html_favicon = html_logo
html_theme = 'furo'
html_static_path = ['_static']
html_theme_options = {
    "navigation_with_keys": True,
    "top_of_page_button": "edit",
    "source_repository": "https://github.com/davidhozic/discord-advertisement-framework/",
    "source_branch": "develop",
    "source_directory": "docs/source",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/davidhozic/discord-advertisement-framework/",
            "html": '<svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path></svg>',
            "class": "",
        }
    ],
}

# ----------- Latex ----------- #
