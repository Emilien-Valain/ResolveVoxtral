"""ResolveVoxtral entry point.

Copy this file AND the sibling `resolvevoxtral` folder together into
Resolve's Scripts folder -- they must stay side by side. See README.md
for the full step-by-step install instructions.
"""

import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from resolvevoxtral import app

if __name__ == "__main__":
    app.main()
