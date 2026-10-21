"""
excel-serial-date

Convert between Excel serial date numbers and Python dates, correctly handling
both the 1900 (Windows) and 1904 (Macintosh) epoch systems.

Design decisions:
    - Input/output is date-only (no time-of-day). Time fractions are explicitly
      *not* preserved so that serial-to-date conversion loses the fractional part
      rather than silently truncating it in a surprising way.
    - ``from_serial`` accepts ``int`` or ``float``; any fractional part is
      discarded via ``int(serial)``.
    - The 1900 epoch inherits Excel's deliberate 1900-is-a-leap-year bug, which
      means serial 60 is treated as the non-existent 1900-02-29. Excel uses this
      value; we preserve it. Serial 59 is 1900-02-28.
    - The 1904 epoch is offset by four years and one day relative to 1900, so
      serial 0 maps to 1904-01-01.
"""

from .core import (
    from_serial,
    to_serial,
    epoch1900_serial_to_ordinal,
    epoch1900_ordinal_to_serial,
    epoch1904_serial_to_ordinal,
    epoch1904_ordinal_to_serial,
)

__all__ = [
    "from_serial",
    "to_serial",
    "epoch1900_serial_to_ordinal",
    "epoch1900_ordinal_to_serial",
    "epoch1904_serial_to_ordinal",
    "epoch1904_ordinal_to_serial",
]
