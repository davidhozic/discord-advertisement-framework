from __future__ import annotations
from contextlib import suppress
import inspect
import os
import sys

# Set current working directory to scripts folder
os.chdir(os.path.dirname(__file__))


sys.path.append(os.path.abspath("../../src"))
sys.argv.append("DOCUMENTATION")
import daf


CATEGORY_TEMPLATE = \
"""
------------------------
{category_name}
------------------------
"""

AUTO_FUNCTION_TEMPLATE =\
"""
{function_name}
========================
.. autofunction:: {module}.{function_name}
"""

AUTO_CLASS_TEMPLATE =\
"""

{class_name}
========================
.. autoclass:: {class_path}
    :members:

    {properties}
"""

MANUAL_FUNCTION_TEMPLATE = \
"""
{function_name}
========================
.. function:: {module}.{function_name}({annotations})
    {docstring}

"""


titles = daf.misc.doc_titles
export_c = ""
export_f = ""
for category, items in titles.items():
    export_c_items = ""
    export_f_items = ""
    for item, manual in items:
        if inspect.isfunction(item):
            if manual:
                export_f_items += MANUAL_FUNCTION_TEMPLATE.format(module=item.__module__, function_name=item.__name__, annotations=",".join(f"{k}: {v}" for k, v in item.__annotations__.items()), docstring=item.__doc__) + "\n"
            else:
                export_f_items += AUTO_FUNCTION_TEMPLATE.format(module=item.__module__, function_name=item.__name__) + "\n"
        elif inspect.isclass(item):
            # Fill properties 
            properties = []
            cls_path = f"{item.__module__}.{item.__name__}"
            for name in dir(item):
                attr = getattr(item, name)
                if isinstance(attr, property):
                    properties.append(f".. autoproperty:: {cls_path}.{name}")

            export_c_items += AUTO_CLASS_TEMPLATE.format(class_name=item.__name__, class_path=cls_path, properties="\n\n    ".join(properties)) + "\n"

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
    
