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
import sys
import os

sys.path.insert(0, os.path.abspath('../../src/'))
sys.path.insert(0, os.path.abspath('.'))
sys.path.append(os.path.abspath("./ext/"))

from daf import VERSION


language = os.environ["LANGUAGE"]

root_doc = f"{language}/index"
exclude_patterns = ["sl/**", "en/**"]

exclude_patterns.remove(f"{language}/**")

# -- Project information -----------------------------------------------------
project = "daf-thesis"
copyright = '2023, David Hozic'
author = 'David Hozic'
version = VERSION


# -- General configuration ---------------------------------------------------
numfig = True

rst_epilog = r"""
.. raw:: latex

    \newpage
"""

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
    "sphinxcontrib.inkscapeconverter",
]


source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

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
    'PyCord': ("https://docs.pycord.dev/en/v2.4.x/", None),
    "DAF": ("https://daf.davidhozic.com/en/v2.9.x/", None),
    "Python": ("https://docs.python.org/3/", None),
    "Sphinx": ("https://www.sphinx-doc.org/en/master", None),
    "SQLAlchemy": ("https://docs.sqlalchemy.org/en/20/", None),
}



# ----------- HTML ----------- #
html_title = project
html_logo = "./DEP/logo.png"
html_favicon = html_logo
html_theme = 'furo'
html_static_path = ['_static']
html_theme_options = {
    "navigation_with_keys": True,
    "top_of_page_button": "edit",
    "source_repository": "https://github.com/davidhozic/discord-advertisement-framework/",
    "source_branch": "master",
    "source_directory": "docs/thesis",
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
with open(f"./{language}/titlepage.tex", "r", encoding="utf-8") as reader:
    latex_title_page = reader.read()

literal_block_str = {
    "en": r"\listof{literalblock}{Literal blocks}",
    "sl": r"\listof{literalblock}{Bloki kode}"
}

latex_theme = "manual"  # latex class => report
latex_elements = {
    "figure_align": "H",
    "sphinxsetup": r"VerbatimColor={rgb}{1,1,1},verbatimhintsturnover=false",
    "papersize": "a4paper",
    "pointsize": "12pt",
    "extraclassoptions": "openright",
    "tableofcontents": r"""
        \tableofcontents
        \newpage
        \listoffigures
        \newpage
        {}
    """.format(literal_block_str.get(language)),
    "fncychap": "",
    "babel": r"\usepackage[slovene]{babel}",
    "inputenc": r"\usepackage[utf8]{inputenc}",
    'preamble':
        r'''
        % Packages
        \usepackage[final]{pdfpages}

        % Spacing
        \textheight 215mm
        \textwidth 145mm
        \oddsidemargin  13mm
        \topmargin -5mm
        \headsep 20mm
        \headheight 6mm
        \evensidemargin 0mm
        \linespread{1.2}

        % Titles (titlesec)
        \titleformat{\chapter}[hang]{\normalfont\Huge\bfseries}{\thechapter}{0.5cm}{}

        % Header and footer
        \usepackage{fancyhdr}
        \pagestyle{fancy}
        \fancypagestyle{normal}{
            \fancyfoot[RE]{{\nouppercase{\leftmark}}}
        }

        % New commands
        \newcommand\blankpage{
            \newpage
            \thispagestyle{empty}
            \mbox{}
            \newpage
        }
    ''',
    "maketitle": rf"""
        \includepdf{{NaslovnaStranDiplome.pdf}}
        \blankpage
        \includepdf{{IzjavaOAvtorstvu.pdf}}
        \blankpage
        {latex_title_page}
        \blankpage
        \pagenumbering{{roman}}
    """,
    "printindex": ''
}

numfig_format = {
    "sl": {
        "figure": "Slika %s",
        "table": "Tabela %s",
        "code-block": "Blok kode %s"
    },
}

if language == "en":
    del numfig_format
else:
    numfig_format = numfig_format[language]


latex_additional_files = ["./NaslovnaStranDiplome.pdf", "./IzjavaOAvtorstvu.pdf"]


# ----------- Docx ----------- #
docx_documents = [
    (f'{language}/index', 'docxbuilder.docx', {}, True),
]
