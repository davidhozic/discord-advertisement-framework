from contextlib import suppress
import inspect
import os
import sys

# Set current working directory to scripts folder
os.chdir(os.path.dirname(__file__))


sys.path.append(os.path.abspath("../../src"))
import discron

FUNCTION_TEMPLATE =\
"""
{function_name}
--------------------------
.. autofunction:: {module}.{function_name}
"""

CLASS_TEMPLATE =\
"""

{class_name}
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: {class_path}
    :members:

    {properties}
"""


export_f = ""
export_c = ""
for item in inspect.getmembers(discron, lambda x: inspect.isclass(x) or inspect.isfunction(x)):
    name, item = item
    if not name.startswith(("_", "Base")):
        if inspect.isfunction(item):
            export_f += FUNCTION_TEMPLATE.format(module= item.__module__, function_name=item.__name__) + "\n"
        elif inspect.isclass(item):
            # Fill properties 
            properties = []
            cls_path = f"{item.__module__}.{item.__name__}"
            for name in dir(item):
                attr = getattr(item, name)
                if isinstance(attr, property):
                    properties.append(f".. autoproperty:: {cls_path}.{name}")

            export_c += CLASS_TEMPLATE.format(class_name=item.__name__, class_path=cls_path, properties="\n\n    ".join(properties)) + "\n"
            


with open("__autodoc_export_funct.rst", "w") as f:
    f.write(export_f)

with open("__autodoc_export_class.rst", "w") as f:
    f.write(export_c)
    
