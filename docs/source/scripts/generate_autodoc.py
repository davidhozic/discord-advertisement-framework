from __future__ import annotations
from contextlib import suppress
from enum import EnumMeta
import inspect
import os
import sys
import re
import pathlib
from typing import List

OUTPUT_PATH = "../reference"

# Set current working directory to scripts folder
os.chdir(os.path.dirname(__file__))


sys.path.append(os.path.abspath("../../../src"))
os.environ["DOCUMENTATION"] = "True"
import daf


CATEGORY_TEMPLATE = \
"""
============================
{category_name}
============================
"""

AUTO_FUNCTION_TEMPLATE =\
"""
------------------------
{object_name}
------------------------
.. autofunction:: {object_path}
"""

AUTO_CLASS_TEMPLATE =\
"""
------------------------
{object_name}
------------------------
.. autoclass:: {object_path}
    :members:
    :inherited-members:
"""

AUTO_ENUM_TEMPLATE =\
"""
------------------------
{object_name}
------------------------
.. autoenum:: {object_path}
    :members:
"""

MANUAL_FUNCTION_TEMPLATE = \
"""
------------------------
{object_name}
------------------------
.. function:: {object_path}({annotations}) -> {return_}
    {_async_}

    {docstring}
"""

titles = daf.misc.doc_titles
output_dir = pathlib.Path(OUTPUT_PATH)
output_dir.mkdir(parents=True, exist_ok=True)
with open(os.path.join(OUTPUT_PATH, "index.rst"), "w", encoding="utf-8") as tocwriter:
    tocwriter.write(
        "=======================\n"
        "Programming Reference\n"
        "=======================\n"
        "Contain classes and functions description.\n"
        "\n"
        ".. toctree::\n\n")

    for category, items in titles.items():
        export_c_items = ""
        export_f_items = ""
        for item, manual, path in items:
            object_name = item.__name__
            object_path = f"{item.__module__}.{object_name}" if path is None else f"daf.{path}.{object_name}"
            if inspect.isfunction(item):
                if manual:
                    _async_ = ":async:" if inspect.iscoroutinefunction(item) else ""
                    annotations = item.__annotations__
                    return_ano = annotations.pop("return")
                    doc_str = inspect.cleandoc(item.__doc__)
                    # Replace titles with list titles
                    doc_str_titles = re.findall(r"[A-z]+\n-+", doc_str)
                    # Replace numpy style lists
                    numpy_list = []
                    numpy_found = re.findall(r"^\w+.*\n {2,}.+", doc_str, re.MULTILINE)
                    for param in numpy_found:
                        split_ = param.split(':')
                        if len(split_) == 2:  # Parameter
                            name, type_desc = split_
                            type_, desc = [x.strip() for x in type_desc.split('\n')]
                            numpy_list.append(f":param {name}: {desc}\n:type {name}: {type_}")
                        else:
                            type_desc = split_[0]
                            type_, desc = [x.strip() for x in type_desc.split('\n')]
                            numpy_list.append(f":raises {type_}: {desc}")
                    
                    for title in doc_str_titles:
                        doc_str = doc_str.replace(title, "")

                    for i, numpy in enumerate(numpy_found):
                        doc_str = doc_str.replace(numpy, numpy_list[i])
                        
                    export_f_items += MANUAL_FUNCTION_TEMPLATE.format(object_name=object_name,
                                                                      _async_=_async_,
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
                    export_c_items += AUTO_CLASS_TEMPLATE.format(object_name=object_name, object_path=object_path) + "\n"


        if export_f_items or export_c_items:
            toc_entry = f"{category.lower().replace(' ', '_')}"
            file_name = os.path.join(OUTPUT_PATH, f"{toc_entry}.rst")
            toc_entry = f"    {toc_entry}\n" 
            with open(file_name, "w", encoding="utf-8") as writer:
                writer.write(CATEGORY_TEMPLATE.format(category_name=category))
                writer.write(export_f_items)
                writer.write(export_c_items)
            
            tocwriter.write(toc_entry)
   
