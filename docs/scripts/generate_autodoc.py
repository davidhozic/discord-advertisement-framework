from __future__ import annotations
from contextlib import suppress
from enum import EnumMeta
import inspect
import os
import sys
import re
from typing import List

# Set current working directory to scripts folder
os.chdir(os.path.dirname(__file__))


sys.path.append(os.path.abspath("../../src"))
sys.argv.append("DOCUMENTATION")
import daf


CATEGORY_TEMPLATE = \
"""
----------------------------
{category_name}
----------------------------
"""

AUTO_FUNCTION_TEMPLATE =\
"""
{object_name}
========================
.. autofunction:: {object_path}
"""

AUTO_CLASS_TEMPLATE =\
"""
{object_name}
========================
.. autoclass:: {object_path}
    :members:

    {properties}
"""

AUTO_ENUM_TEMPLATE =\
"""
{object_name}
========================
.. autoenum:: {object_path}
    :members:
"""

MANUAL_FUNCTION_TEMPLATE = \
"""
{object_name}
========================
.. function:: {object_path}({annotations}) -> {return_}
    
    {docstring}
"""



titles = daf.misc.doc_titles
export_c = "===============================\nClasses\n===============================\n"
export_f = "===============================\nFunctions\n===============================\n"
for category, items in titles.items():
    export_c_items = ""
    export_f_items = ""
    for item, manual, path in items:
        object_name = item.__name__
        object_path = f"{item.__module__}.{object_name}" if path is None else f"daf.{path}.{object_name}"
        if inspect.isfunction(item):
            if manual:
                annotations = item.__annotations__
                return_ano = annotations.pop("return")
                doc_str = inspect.cleandoc(item.__doc__)
                # Replace titles with list titles
                doc_str_titles = re.findall(r"[A-z]+\n-+", doc_str)
                # Replace numpy style lists
                numpy_list: List[str] = re.findall(r".+\n {2,}.+", doc_str)

                for title in doc_str_titles:
                    new_title = f':{re.sub(r"-{2,}", "", title).strip()}:'
                    doc_str = doc_str.replace(title, new_title)

                for numpy in numpy_list:
                    title, desc = numpy.split("\n")
                    title = f"    - {title}"
                    desc = f"      {desc}"
                    doc_str = doc_str.replace(numpy, f"{title}\n{desc}")

                export_f_items += MANUAL_FUNCTION_TEMPLATE.format(object_name=object_name,
                                                                  annotations=",".join(f"{k}: {v}" for k, v in annotations.items()),
                                                                  object_path=object_path,
                                                                  docstring="\n    ".join(doc_str.splitlines()),
                                                                  return_=return_ano) + "\n"
            else:
                export_f_items += AUTO_FUNCTION_TEMPLATE.format(object_name=object_name, object_path=object_path,) + "\n"
        elif inspect.isclass(item):
            # Fill properties 
            if isinstance(item, EnumMeta):
                export_c_items += AUTO_ENUM_TEMPLATE.format(object_name=object_name, object_path=object_path) + "\n"
            else:
                properties = []
                for name in dir(item):
                    attr = getattr(item, name)
                    if isinstance(attr, property):
                        properties.append(f".. autoproperty:: {object_path}.{name}")

                export_c_items += AUTO_CLASS_TEMPLATE.format(object_name=object_name, object_path=object_path, properties="\n\n    ".join(properties)) + "\n"


    if export_f_items:
        export_f += CATEGORY_TEMPLATE.format(category_name=category)
        export_f += export_f_items
    
    if export_c_items:
        export_c += CATEGORY_TEMPLATE.format(category_name=category)
        export_c += export_c_items


with open("__autodoc_export_funct.rst", "w") as f:
    f.write(export_f)

with open("__autodoc_export_class.rst", "w") as f:
    f.write(export_c)
    
