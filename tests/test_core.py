import unittest
from datetime import date

from excel_serial_date import (
    from_serial,
    to_serial,
    epoch1900_serial_to_ordinal,
    epoch1900_ordinal_to_serial,
    epoch1904_serial_to_ordinal,
    epoch1904_ordinal_to_serial,
)


class TestEpoch1900Forward(unittest.TestCase):
    def test_serial_1_is_1900_01_01(self):
        self.assertEqual(from_serial(1), date(1900, 1, 1))

    def test_serial_59_is_1900_02_28(self):
        self.assertEqual(from_serial(59), date(1900, 2, 28))

    def test_serial_61_is_1900_03_01(self):
        # The fictitious 1900-02-29 is skipped: 61, not 60, is 1900-03-01.
        self.assertEqual(from_serial(61), date(1900, 3, 1))

    def test_serial_367_is_1901_01_01(self):
        self.assertEqual(from_serial(367), date(1901, 1, 1))

    def test_modern_roundtrip_2023(self):
        d = date(2023, 6, 15)
        self.assertEqual(to_serial(d, epoch="1900"), 45092)
        self.assertEqual(from_serial(45092), d)


class TestEpoch1900GhostDay(unittest.TestCase):
    def test_from_serial_60_raises(self):
        with self.assertRaises(ValueError):
            from_serial(60)

    def test_serial_to_ordinal_60_raises(self):
        with self.assertRaises(ValueError):
            epoch1900_serial_to_ordinal(60)

    def test_feb_29_1900_raises(self):
        # proleptic Gregorian rejects 1900-02-29 at construction time.
        with self.assertRaises(ValueError):
            date(1900, 2, 29)

    def test_serial_skip_59_to_61(self):
        self.assertEqual(epoch1900_serial_to_ordinal(59), date(1900, 2, 28).toordinal())
        self.assertEqual(epoch1900_serial_to_ordinal(61), date(1900, 3, 1).toordinal())


class TestEpoch1900Reverse(unittest.TestCase):
    def test_1900_01_01_is_serial_1(self):
        self.assertEqual(to_serial(date(1900, 1, 1), epoch="1900"), 1)

    def test_1900_02_28_is_serial_59(self):
        self.assertEqual(to_serial(date(1900, 2, 28), epoch="1900"), 59)

    def test_1900_03_01_is_serial_61(self):
        self.assertEqual(to_serial(date(1900, 3, 1), epoch="1900"), 61)

    def test_from_ordinal(self):
        self.assertEqual(epoch1900_ordinal_to_serial(date(1901, 1, 1).toordinal()), 367)


class TestEpoch1904(unittest.TestCase):
    def test_serial_0_is_1904_01_01(self):
        self.assertEqual(from_serial(0, epoch="1904"), date(1904, 1, 1))

    def test_serial_1_is_1904_01_02(self):
        self.assertEqual(from_serial(1, epoch="1904"), date(1904, 1, 2))

    def test_modern_roundtrip_2024(self):
        d = date(2024, 2, 29)  # real leap year
        self.assertEqual(to_serial(d, epoch="1904"), 43889)
        self.assertEqual(from_serial(43889, epoch="1904"), d)

    def test_1904_has_no_ghost_day(self):
        # Serial 60 should be a normal day, 1904-03-01, NOT a raised ValueError.
        self.assertEqual(from_serial(60, epoch="1904"), date(1904, 3, 1))

    def test_reverse_via_ordinal_helpers(self):
        self.assertEqual(epoch1904_serial_to_ordinal(0), date(1904, 1, 1).toordinal())
        self.assertEqual(
            epoch1904_ordinal_to_serial(date(1904, 1, 1).toordinal()), 0
        )


class TestFloatInput(unittest.TestCase):
    def test_float_discards_fraction(self):
        self.assertEqual(from_serial(61.999), date(1900, 3, 1))

    def test_float_1904(self):
        self.assertEqual(from_serial(1.5, epoch="1904"), date(1904, 1, 2))


class TestErrors(unittest.TestCase):
    def test_unknown_epoch_from(self):
        with self.assertRaises(ValueError):
            from_serial(1, epoch="2000")

    def test_unknown_epoch_to(self):
        with self.assertRaises(ValueError):
            to_serial(date(2000, 1, 1), epoch="2000")

    def test_serial_below_1900_minimum(self):
        with self.assertRaises(ValueError):
            from_serial(0)

    def test_serial_below_1904_minimum(self):
        with self.assertRaises(ValueError):
            from_serial(-1, epoch="1904")

    def test_to_serial_before_1900_epoch(self):
        with self.assertRaises(ValueError):
            to_serial(date(1899, 12, 31), epoch="1900")

    def test_to_serial_before_1904_epoch(self):
        with self.assertRaises(ValueError):
            to_serial(date(1903, 12, 31), epoch="1904")


class TestConsistency(unittest.TestCase):
    def test_known_excel_reference_values_1900(self):
        # These serials are what Excel shows on a 1900-epoch workbook.
        cases = [
            (44927, date(2023, 1, 1)),
            (45292, date(2024, 1, 1)),
            (45658, date(2025, 1, 1)),
        ]
        for serial, expected in cases:
            with self.subTest(serial=serial):
                self.assertEqual(from_serial(serial), expected)
                self.assertEqual(to_serial(expected, epoch="1900"), serial)

    def test_roundtrip_1904(self):
        # The 1904 system is a fixed +1462-day offset relative to 1900; check
        # that the serial difference matches for the same calendar date.
        d = date(2023, 6, 15)
        self.assertEqual(to_serial(d, epoch="1900") - to_serial(d, epoch="1904"), 1462)


if __name__ == "__main__":
    unittest.main()
