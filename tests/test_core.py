import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location("pi_core", Path(__file__).resolve().parent.parent / "core.py")
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)


class InitialsTests(unittest.TestCase):
    def test_initials_of_reads_the_trailing_parenthetical(self):
        self.assertEqual(core.initials_of("Billing Service (bs)"), "bs")
        self.assertEqual(core.initials_of("Billing Service (BS)"), "bs")
        self.assertIsNone(core.initials_of("Billing Service"))
        self.assertIsNone(core.initials_of("(bs) Billing Service"))

    def test_derive_two_letters_from_first_two_words(self):
        self.assertEqual(core.derive_initials("Billing Service"), "bs")
        self.assertEqual(core.derive_initials("Billing — Service Desk"), "bs")
        self.assertEqual(core.derive_initials("Backup"), "ba")

    def test_derive_adds_a_third_letter_only_on_collision(self):
        self.assertEqual(core.derive_initials("Billing Service", taken={"bs"}), "bse")
        self.assertEqual(core.derive_initials("Backup", taken={"ba"}), "bac")

    def test_initials_map_prefers_explicit_and_avoids_their_codes(self):
        names = ["Billing Service (bs)", "Big Sky", "Plain"]
        self.assertEqual(core.initials_map(names), {"Billing Service (bs)": "bs"})
        derived = core.initials_map(names, derive_missing=True)
        self.assertEqual(derived["Billing Service (bs)"], "bs")
        self.assertEqual(derived["Big Sky"], "bsk")  # "bs" is taken
        self.assertEqual(derived["Plain"], "pl")


class ShortenTests(unittest.TestCase):
    def test_zero_keeps_the_topic(self):
        self.assertEqual(core.shorten("Fix the invoice rounding bug", 0), "Fix the invoice rounding bug")

    def test_caps_words_and_drops_fillers(self):
        self.assertEqual(core.shorten("Comp map in full report", 2), "Comp map")
        self.assertEqual(core.shorten("The invoice rounding bug", 2), "Invoice rounding")

    def test_first_clause_only(self):
        self.assertEqual(core.shorten("Fix totals. Then check the export", 3), "Fix totals")

    def test_drops_project_words_when_something_meaningful_is_left(self):
        drop = core.project_words("Billing Service (bs)", "bs")
        self.assertEqual(core.shorten("Billing service invoice fix", 2, drop), "Invoice fix")
        self.assertEqual(core.shorten("Billing service", 2, drop), "Billing service")


class PrefixedTitleTests(unittest.TestCase):
    INI = {"Billing Service (bs)": "bs", "Mobile App (ma)": "ma"}

    def title(self, title, project="Billing Service (bs)", **kw):
        return core.prefixed_title(title, project, self.INI, **kw)

    def test_prefix_in_capitals_by_default(self):
        self.assertEqual(self.title("Fix invoices"), "BS: Fix invoices")

    def test_lowercase_when_asked(self):
        self.assertEqual(self.title("Fix invoices", uppercase=False), "bs: Fix invoices")

    def test_other_projects_prefix_is_replaced_not_stacked(self):
        self.assertEqual(self.title("ma: Fix invoices"), "BS: Fix invoices")
        self.assertEqual(self.title("MA: Fix invoices"), "BS: Fix invoices")

    def test_idempotent(self):
        once = self.title("Fix invoices")
        self.assertEqual(self.title(once), once)

    def test_ordinary_capitalised_word_is_not_a_prefix(self):
        self.assertEqual(self.title("Fix: invoices"), "BS: Fix: invoices")

    def test_no_project_or_no_initials_leaves_the_title(self):
        self.assertEqual(self.title("Fix invoices", project=None), "Fix invoices")
        self.assertEqual(self.title("Fix invoices", project="Unknown"), "Fix invoices")

    def test_collision_suffix_is_dropped_and_length_capped(self):
        self.assertEqual(self.title("Fix invoices #2"), "BS: Fix invoices")
        out = self.title("word " * 60, max_len=40)
        self.assertLessEqual(len(out), 40)

    def test_word_cap_and_project_word_trim(self):
        self.assertEqual(self.title("Billing service invoice fix now", max_words=2, drop_project_words=True),
                         "BS: Invoice fix")


if __name__ == "__main__":
    unittest.main()
