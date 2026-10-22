# excel-serial-date

Converts between Excel serial date numbers and Python `datetime.date` objects, correctly handling both the 1900 (Windows) and 1904 (Macintosh) epoch systems — including Excel's deliberate 1900-is-a-leap-year bug.

```python
from datetime import date
from excel_serial_date import from_serial, to_serial

# 1900 epoch (Windows default)
d = from_serial(45102)      # -> date(2023, 6, 15)
n = to_serial(date(2023, 6, 15))          # -> 45102

# 1904 epoch (classic Mac)
d = from_serial(43640, epoch="1904")      # -> date(2023, 6, 15)
n = to_serial(date(2023, 6, 15), epoch="1904")  # -> 43640
```

Exported names: `from_serial`, `to_serial`, and four lower-level helpers (`epoch1900_serial_to_ordinal`, `epoch1900_ordinal_to_serial`, `epoch1904_serial_to_ordinal`, `epoch1904_ordinal_to_serial`) for callers who want proleptic Gregorian ordinals directly.

## Why this exists

Excel's 1900 epoch inherits a bug from Lotus 1-2-3: it treats 1900 as a leap year. In Excel's 1900 system, serial 60 is the non-existent date 1900-02-29, and serials 61 onward are therefore one day ahead of a naive "1900-01-01 plus N days" calculation. The 1904 epoch (used by classic Mac Excel) starts at 1904-01-01 as serial 0 and does **not** carry the fictitious leap day. A correct converter must apply a one-day correction only for 1900-epoch serials at or above 61, and must never apply it under the 1904 epoch.

This library implements exactly those two epoch systems and nothing else. Times of day (the fractional part of an Excel serial) are deliberately discarded rather than silently truncated: `from_serial` accepts floats but uses `int(serial)`, so if you pass `61.5` you get `1900-03-01` with no warning. If you need sub-day precision, parse the fractional part yourself before calling this library — that boundary is intentionally left to the caller so the function's contract is unambiguous.

## The awkward edge

Under the 1900 epoch, `from_serial(60)` raises `ValueError`. Serial 60 is Excel's fictitious 1900-02-29, and the proleptic Gregorian calendar used by Python's `date` has no such day. There is no value of `date` that can represent it, so the library refuses rather than returning a wrong answer (such as 1900-02-28 or 1900-03-01). Under the 1904 epoch, serial 60 is a perfectly ordinary day (1904-03-01) and is returned normally.
