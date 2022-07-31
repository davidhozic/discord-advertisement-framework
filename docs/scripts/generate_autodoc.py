from contextlib import suppress
import inspect
import os
import sys

# Set current working directory to scripts folder
for path, dirs, files in os.walk("./"):
    for dir in dirs:
        if dir == "scripts":
            os.chdir(os.path.join(path, dir))
            break


sys.path.append(os.path.abspath("../../src"))
import framework

FUNCTION_TEMPLATE =\
"""
{function_name}
--------------------------
.. autofunction:: framework.{function_name}
"""

CLASS_TEMPLATE =\
"""

{class_name}
~~~~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: framework.{class_name}
    :members:
"""


export_f = ""
export_c = ""
for item in inspect.getmembers(framework, lambda x: inspect.isclass(x) or inspect.isfunction(x)):
    name, item = item
    if not name.startswith(("_", "Base")):
        if inspect.isfunction(item):
            export_f += FUNCTION_TEMPLATE.format(function_name=item.__name__) + "\n"
        elif inspect.isclass(item):
            export_c += CLASS_TEMPLATE.format(class_name=item.__name__) + "\n"


with open("__autodoc_export_funct.rst", "w") as f:
    f.write(export_f)

with open("__autodoc_export_class.rst", "w") as f:
    f.write(export_c)
    
