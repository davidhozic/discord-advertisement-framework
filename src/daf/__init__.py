"""
Discord Advertisement Framework
"""
import _discord as discord
from .client import *
from .core import *
from .dtypes import *
from .guild import *
from .message import *
from .logging import *
from .web import *

from .misc import DOCUMENTATION_MODE
if DOCUMENTATION_MODE:
    from .misc import *

import os
# Parse version
gh_release = os.environ.get("GITHUB_REF_NAME", default=None) # Workflow run release
readthedocs_release = os.environ.get("READTHEDOCS_VERSION", default=None) # Readthe docs version

VERSION = "v0.0.1"
if gh_release is not None:
    VERSION = gh_release
elif readthedocs_release is not None:
    VERSION = readthedocs_release

VERSION = VERSION.removeprefix("v")
del os
