==========
Methods
==========

.. _DAF_WEB: https://daf.davidhozic.com

.. _sphinx.ext.autodoc: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

.. |DAF_WEB| replace:: DAF's website


Documentation
=====================
The entire thesis project is well documented.
The documentation is primary built to HTML and published to |DAF_WEB|_.

Sphinx
----------
The system used for documenting code is called Sphinx.
Sphinx is a popular tool among Python developers for generating documentation.
It is written in Python and can be used in a variety of environments.
This documentation generator allows developers to create professional-quality documentation for their projects, 
which is essential for effective communication and collaboration within the software development process.
Sphinx makes it easy to document Python code, with support for docstrings and other markup languages.
It also provides formatting options and can generate documentation in a range of output formats, including HTML, LaTeX, and PDF.
In addition, Sphinx offers extensive customization options,
allowing developers to tailor the appearance and functionality of their documentation to meet their specific needs.
Overall, Sphinx is a valuable tool for Python developers looking to create comprehensive,
user-friendly documentation for their projects.

Sphinx primarily uses restructuredText for markup, but it also supports Markdown. 
For writing equations you can write in Latex.

reStructuredText
------------------
reStructuredText is a popular markup language used within the Python programming community for documentation.
It is designed to be easily readable, with a focus on simplicity and power.
The syntax allows for the creation of web pages and standalone documents, as well as in-line program documentation such as Python docstrings.
One of the key features of reStructuredText is its extensibility, which allows it to be customized for specific application domains.

Within the reStructuredText syntax, there are various roles and directives that can be used to add formatting and structure to documents.
Roles are used to apply formatting to specific words or phrases,
while directives are used to add structure or additional information to the document.
These tools allow users to create more complex and polished documents, 
while still maintaining the simplicity and readability of the reStructuredText syntax.

.. code-block:: reStructuredText
    :caption: reStructuredText directive example

    .. figure:: img/rickroll.png
        :scale: 50%

        Rickroll image


.. code-block:: reStructuredText
    :caption: reStructuredText role example

    :math:`\int 1 dx = x + C`


Documenting the project
---------------------------
DAF is fully documented using the Sphinx build system. 

The guide for using DAF is written in .rst files located under the ``/project root/docs/source/guide`` folder in the language
restructuredText.

In some directories, files named "dep_local.json" can be found. These are setup configurations
that contain a list of files to copy and scripts to run before building the documentation.
For example the ``/project root/docs/source/dep_local.json`` directory has the following dictionary:

.. literalinclude:: DEP/source/dep_local.json
    :caption: Documentation setup file (dep_local.json)

The above file tells the setup.py script to copy DAF's logo to a local ``DEP/`` folder and run the script
``generate_autodoc.py``.

The script ``generate_autodoc.py`` is responsible for generating DAF's API reference which includes all the 
function / class (and it's methods) descriptions.
The script knows what to generate based on a decorator named :func:`~daf.misc.doc_category` that is used at each function and class
that is to be automatically documented.

.. autofunction:: daf.misc.doc_category

.. raw:: latex

    \newpage

.. code-block:: python
    :caption: Usage of the :func:`~misc.doc_category` decorator.

    @misc.doc_category("Logging reference", path="logging.sql")
    class LoggerSQL(logging.LoggerBASE):
        ...

All the functions and classes that were marked with the above decorator, will have generated either 
a ``autofunction`` directive, ``autoclass`` directive or just regular ``function`` if the ``manual`` parameter is set to True.
If the latter, it also has the body filled based on regex matches that are then transformed into normal Sphinx-styled function docstring.
Only functions with a ``@overload`` decorator above them have the ``manual`` parameter set to ``True``, since Sphinx
cannot fully document those types of functions.

The generated ``autofunction`` / ``autoclass`` directives are part of Sphinx's extension called `sphinx.ext.autodoc`_.
Autodoc imports the package and extract the function / class docstring and then creates a nice looking
description. If you use the ``:members:`` option under ``autoclass``, it will also generate descriptions for all the methods and attributes
that have a docstring attached to them.


.. code-block:: restructuredText
    :caption: Example of an auto-generated API reference

    ============================
    Dynamic mod.
    ============================

    ------------------------
    add_object
    ------------------------
    .. function:: daf.core.add_object(obj: <class 'daf.client.ACCOUNT'>) -> None
        
        Adds an account to the framework.
        
        
        :param obj: The account object to add
        :type obj: client.ACCOUNT
        
        
        :raises ValueError: The account has already been added to the list.
        :raises TypeError: ``obj`` is of invalid type.


    ============================
    Clients
    ============================

    ------------------------
    get_accounts
    ------------------------
    .. autofunction:: daf.core.get_accounts


    ------------------------
    ACCOUNT
    ------------------------
    .. autoclass:: daf.client.ACCOUNT
        :members:

.. raw:: latex

    \newpage

The above would result in the following:

.. image:: ./images/autodoc_example1.png
    :width: 400
    :align: center

.. figure:: ./images/autodoc_example2.png
    :width: 400
    :align: center

    Automatic documentation output example

