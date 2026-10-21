"""
Core conversion functions for Excel serial dates.

Excel stores dates as integer serial numbers counting days from an epoch.
There are two common epoch systems:

    * 1900 epoch (Windows default): day 1 is 1900-01-01.
      Excel also, for backwards compatibility with Lotus 1-2-3, treats 1900 as a
      leap year. So serial 60 represents the fictitious date 1900-02-29 and the
      calendar skips directly from serial 59 (1900-02-28) to serial 61
      (1900-03-01). This means every serial >= 61 is one day *later* in reality
      than a naive 1900-01-01 + (n - 1) calculation would produce.

    * 1904 epoch (classic Mac): day 0 is 1904-01-01. This system does NOT carry
      the 1900 leap-year bug because 1904 was genuinely a leap year, so no
      fictitious day is introduced.

Python's ``datetime.date`` uses a *proleptic Gregorian* calendar with ordinal
1 = 0001-01-01. We bridge between the two by adding/subtracting a fixed offset.
For the 1900 epoch we cannot use a single constant offset because of the
fictitious 1900-02-29: days 1..59 use one offset, days 60.. use another.
"""

from __future__ import annotations

from datetime import date

# Proleptic Gregorian ordinal of 1900-01-01. date.toordinal() would give us
# this; hard-coding it avoids depending on a library call for setup and keeps
# the constant self-documenting. Verified: date(1900, 1, 1).toordinal() == 693596.
_ORDINAL_1900_01_01 = 693596

# Excel serial 1 maps to 1900-01-01, so the naive offset is ordinal(serial) =
# _ORDINAL_1900_01_01 + (serial - 1) = _ORDINAL_1900_01_01 - 1 + serial.
# Therefore the constant term (without the +serial) is _ORDINAL_1900_01_01 - 1.
_BASE_OFFSET_1900 = _ORDINAL_1900_01_01 - 1  # == 693595

# Because Excel treats 1900-02-29 (serial 60) as real, every serial >= 61 is
# one day ahead of the proleptic calendar. To correct for the ghost day we
# subtract 1 from the naive offset for serials 61 and above. Serial 60 itself
# cannot be represented and is handled out-of-band.
# Combined offset for serials >= 61: _BASE_OFFSET_1900 - 1 == 693594.
_OFFSET_1900_POST_GHOST = _BASE_OFFSET_1900 - 1  # == 693594

# The 1904 epoch is 1462 days after the 1900 epoch's day 0:
#   date(1904, 1, 1).toordinal() - date(1899, 12, 30).toordinal() == 1462.
# Since 1904-01-01 falls after the 1900 ghost day, we anchor on the post-ghost
# offset. Verified: date(1904, 1, 1).toordinal() == 695056.
_OFFSET_1904_BASE = _OFFSET_1900_POST_GHOST + 1462  # == 695056

# Under the 1904 system serial 0 == 1904-01-01. Excel does NOT propagate the
# 1900 leap bug into the 1904 system, so a single constant offset suffices.

# Bounds for the 1900 ghost-day region.
_SERIAL_1900_GHOST = 60
_SERIAL_1900_LAST_REAL_BEFORE_GHOST = 59


def epoch1900_serial_to_ordinal(serial: int) -> int:
    """Convert a 1900-epoch Excel serial integer to a proleptic Gregorian ordinal.

    Serials 1..59 map linearly to 1900-01-01 .. 1900-02-28.
    Serial 60 is Excel's fictitious 1900-02-29 and has no proleptic Gregorian
    representation; ``ValueError`` is raised.
    Serials 61.. are shifted back by one to skip the ghost day, so serial 61
    is 1900-03-01, serial 367 is 1901-01-01, and so on.
    """
    if serial < 1:
        raise ValueError("1900-epoch serials must be >= 1")
    if serial == _SERIAL_1900_GHOST:
        raise ValueError(
            "serial 60 is the fictitious 1900-02-29 created by Excel's "
            "1900 leap-year bug; it has no proleptic Gregorian representation"
        )
    if serial <= _SERIAL_1900_LAST_REAL_BEFORE_GHOST:
        return _BASE_OFFSET_1900 + serial
    return _OFFSET_1900_POST_GHOST + serial


def epoch1900_ordinal_to_serial(ordinal: int) -> int:
    """Convert a proleptic Gregorian ordinal to a 1900-epoch Excel serial integer.

    The inverse of :func:`epoch1900_serial_to_ordinal`. The proleptic calendar
    contains no 1900-02-29, so the returned serial skips 60; ordinals up to and
    including that of 1900-02-28 map to serials 1..59, and the ordinal of
    1900-03-01 maps to serial 61.
    """
    if ordinal < _ORDINAL_1900_01_01:
        raise ValueError("1900-epoch serials start at 1 (1900-01-01)")
    ordinal_of_feb_28_1900 = date(1900, 2, 28).toordinal()
    if ordinal <= ordinal_of_feb_28_1900:
        return ordinal - _BASE_OFFSET_1900
    # ordinal is at least that of 1900-03-01, so the serial skips the ghost 60.
    return ordinal - _OFFSET_1900_POST_GHOST


def epoch1904_serial_to_ordinal(serial: int) -> int:
    """Convert a 1904-epoch Excel serial integer to a proleptic Gregorian ordinal.

    The 1904 epoch begins at 1904-01-01 as serial 0. Unlike the 1900 system,
    Excel does not introduce a fictitious leap day here, so the mapping is a
    single affine shift.
    """
    if serial < 0:
        raise ValueError("1904-epoch serials must be >= 0")
    return _OFFSET_1904_BASE + serial


def epoch1904_ordinal_to_serial(ordinal: int) -> int:
    """Convert a proleptic Gregorian ordinal to a 1904-epoch Excel serial integer.

    The inverse of :func:`epoch1904_serial_to_ordinal`.
    """
    if ordinal < _OFFSET_1904_BASE:
        raise ValueError("1904-epoch serials start at 0 (1904-01-01)")
    return ordinal - _OFFSET_1904_BASE


def from_serial(serial, *, epoch="1900") -> date:
    """Convert an Excel serial number to a :class:`datetime.date`.

    Parameters
    ----------
    serial:
        The Excel serial number. May be ``int`` or ``float``; any fractional part
        (which would encode a time of day) is discarded via ``int(serial)``.
    epoch:
        Either ``"1900"`` (the Windows default) or ``"1904"`` (the classic
        Macintosh system).

    The 1900-epoch fictitious 1900-02-29 (serial 60) raises ``ValueError``; it
    has no proleptic Gregorian counterpart.
    """
    n = int(serial)
    if epoch == "1900":
        return date.fromordinal(epoch1900_serial_to_ordinal(n))
    if epoch == "1904":
        return date.fromordinal(epoch1904_serial_to_ordinal(n))
    raise ValueError(f"unknown epoch: {epoch!r} (expected '1900' or '1904')")


def to_serial(value, *, epoch="1900") -> int:
    """Convert a date (or ordinal) to an Excel serial integer.

    Parameters
    ----------
    value:
        A :class:`datetime.date` or a proleptic Gregorian ``int`` ordinal.
    epoch:
        Either ``"1900"`` or ``"1904"``.

    Dates before the chosen epoch's start raise ``ValueError``.
    """
    if isinstance(value, date):
        ordinal = value.toordinal()
    else:
        ordinal = int(value)
    if epoch == "1900":
        return epoch1900_ordinal_to_serial(ordinal)
    if epoch == "1904":
        return epoch1904_ordinal_to_serial(ordinal)
    raise ValueError(f"unknown epoch: {epoch!r} (expected '1900' or '1904')")
