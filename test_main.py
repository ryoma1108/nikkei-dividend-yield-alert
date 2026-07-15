import unittest

from date_utils import count_business_days_since_last_notify, normalize_date, sort_market_data


def row(data_date, yield_value="2.04"):
    return ["", data_date, "", "", "", "", yield_value]


class MainTest(unittest.TestCase):
    def test_normalize_date_variants(self):
        self.assertEqual(normalize_date("2026/07/15"), "2026-07-15")
        self.assertEqual(normalize_date("2026-07-15 09:00:00"), "2026-07-15")
        self.assertEqual(normalize_date("2026-07-15T09:00:00"), "2026-07-15")

    def test_sort_market_data_newest_first(self):
        data = [row("2026-07-13"), row("2026-07-15"), row("2026-07-14")]
        sorted_data = sort_market_data(data)
        self.assertEqual([item[1] for item in sorted_data], ["2026-07-15", "2026-07-14", "2026-07-13"])

    def test_count_business_days_since_last_notify_found(self):
        data = [row("2026-07-15"), row("2026-07-14"), row("2026-07-13")]
        count, found = count_business_days_since_last_notify(data, "2026-07-13")
        self.assertTrue(found)
        self.assertEqual(count, 2)

    def test_count_business_days_same_data_date(self):
        data = [row("2026-07-15"), row("2026-07-14"), row("2026-07-13")]
        count, found = count_business_days_since_last_notify(data, "2026-07-15")
        self.assertTrue(found)
        self.assertEqual(count, 0)

    def test_count_business_days_missing_last_data_date_is_safe(self):
        data = [row("2026-07-15"), row("2026-07-14"), row("2026-07-13")]
        count, found = count_business_days_since_last_notify(data, "2026-07-01")
        self.assertFalse(found)
        self.assertEqual(count, 0)

    def test_count_business_days_accepts_slash_date(self):
        data = [row("2026-07-15"), row("2026-07-14"), row("2026-07-13")]
        count, found = count_business_days_since_last_notify(data, "2026/07/13")
        self.assertTrue(found)
        self.assertEqual(count, 2)

    def test_count_business_days_29_days_before_threshold(self):
        data = [row(f"2026-07-{day:02d}") for day in range(31, 1, -1)]
        count, found = count_business_days_since_last_notify(data, "2026-07-02")
        self.assertTrue(found)
        self.assertEqual(count, 29)
        self.assertLess(count, 30)

    def test_count_business_days_30_days_reaches_threshold(self):
        data = [row(f"2026-07-{day:02d}") for day in range(31, 0, -1)]
        count, found = count_business_days_since_last_notify(data, "2026-07-01")
        self.assertTrue(found)
        self.assertEqual(count, 30)
        self.assertGreaterEqual(count, 30)


if __name__ == "__main__":
    unittest.main()
