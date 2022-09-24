from contextlib import suppress
import inspect
import os
import sys
import re


# Set current working directory to scripts folder
os.chdir(os.path.dirname(__file__))


EXCEPTION_TEMPLATE =\
"""
    {error_name}:
        Value: {error_code}

        Info: {error_message}
"""
# """
# | {error_name}| {error_code}| {error_message}|
# +----------------------------------------+------+----------------------------------------------------------------------------------------------------------------------------+"""


export_e = ".. glossary::\n"
fdata = ""
with open("../../src/daf/exceptions.py", "r") as f:
    fdata += f.read()

excs = re.findall(r"\w+.+#:.+", fdata)

for exc in excs:
    name = re.search(r"[A-z]+", exc).group(0)
    value = re.search(r"[0-9]+", exc).group(0)    
    description = re.search(r"(?<=#:).+", exc).group(0).strip()
    export_e += EXCEPTION_TEMPLATE.format(error_name=name, error_code=value, error_message=description)


with open("__autodoc_export_exceptions.rst", "w") as f:
    f.write(export_e)


