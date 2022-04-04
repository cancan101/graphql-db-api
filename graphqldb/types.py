import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:  # pragma: no cover
    from typing_extensions import TypedDict  # noqa: F401
