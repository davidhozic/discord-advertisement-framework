from contextlib import suppress
import inspect
import os
import sys
import re


with suppress():
    os.chdir("docs/scripts")


EXCEPTION_TEMPLATE =\
""" 
    **{name}**
        :Enumerated value:
            {code}

        :Description:
            {description}
"""


export_e = ""
fdata = ""
with open("../../src/framework/exceptions.py", "r") as f:
    fdata += f.read()

excs = re.findall(r"\w+.+#:.+", fdata)

for exc in excs:
    name = re.search(r"[A-z]+", exc).group(0)
    value = re.search(r"[0-9]+", exc).group(0)
    description = re.search(r"(?<=#:).+", exc).group(0).strip()
    export_e += EXCEPTION_TEMPLATE.format(name=name, code=value, description=description) + "\n"


with open("autodoc_export_exceptions.rst", "w") as f:
    f.write(export_e)


