"""ResolveVoxtral entry point.

Copy this file AND the sibling `resolvevoxtral` folder together into
Resolve's Scripts folder -- they must stay side by side. See README.md
for the full step-by-step install instructions.
"""

import os
import sys


def _script_dir():
    """Return the folder containing this script.

    Resolve's Fusion scripting environment does not always define ``__file__``,
    so fall back to other ways of locating the script before giving up on the
    current working directory.
    """
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        pass

    # sys.argv[0] is set to the script path when Resolve runs it.
    if sys.argv and sys.argv[0]:
        candidate = os.path.dirname(os.path.abspath(sys.argv[0]))
        if candidate:
            return candidate

    # Last resort: the standard Resolve Scripts/Utility location.
    return os.getcwd()


_here = _script_dir()
if _here not in sys.path:
    sys.path.insert(0, _here)

from resolvevoxtral import app

app.main()
