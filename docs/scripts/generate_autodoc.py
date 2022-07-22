from contextlib import suppress
import inspect
import os
import sys


with suppress():
    os.chdir("docs/scripts")

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
    item = item[1]
    if inspect.isfunction(item):
        export_f += FUNCTION_TEMPLATE.format(function_name=item.__name__) + "\n"
    elif inspect.isclass(item):
        export_c += CLASS_TEMPLATE.format(class_name=item.__name__) + "\n"


with open("autodoc_export_funct.rst", "w") as f:
    f.write(export_f)

with open("autodoc_export_class.rst", "w") as f:
    f.write(export_c)
    
