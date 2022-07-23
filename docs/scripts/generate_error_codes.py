from contextlib import suppress
import inspect
import os
import sys
import re


with suppress():
    os.chdir("docs/scripts")


EXCEPTION_TEMPLATE =\
"""
| {error_code}{space_ec}| {error_message}{space_msg}|
+------+----------------------------------------------------------------------------+"""


export_e = "+------+----------------------------------------------------------------------------+"
fdata = ""
with open("../../src/framework/exceptions.py", "r") as f:
    fdata += f.read()

excs = re.findall(r"\w+.+#:.+", fdata)

for exc in excs:
    # name = re.search(r"[A-z]+", exc).group(0)
    value = re.search(r"[0-9]+", exc).group(0)    
    description = re.search(r"(?<=#:).+", exc).group(0).strip()
    export_e += EXCEPTION_TEMPLATE.format(error_code=value, space_ec="".join(' ' for i in range(5-len(value))), error_message=description, space_msg="".join(' ' for i in range(75-len(description))))

export_e += ""


with open("autodoc_export_exceptions.rst", "w") as f:
    f.write(export_e)


