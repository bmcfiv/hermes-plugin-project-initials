import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_plugin():
    spec = importlib.util.spec_from_file_location(
        "project_initials_plugin", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)]
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["project_initials_plugin"] = mod
    spec.loader.exec_module(mod)
    return mod


class Ctx:
    def __init__(self, **settings):
        self.settings = settings
        self.hooks = {}

    def get_config(self, key, default=None):
        return self.settings.get(key, default)

    def register_hook(self, name, fn):
        self.hooks[name] = fn


class HookTests(unittest.TestCase):
    def setUp(self):
        self.plugin = load_plugin()
        self.addCleanup(lambda: [sys.modules.pop(k, None) for k in list(sys.modules) if k.startswith("project_initials_plugin")])
        self.names = ["Billing Service (bs)", "Mobile App (ma)", "Plain"]
        self.owner = "Billing Service (bs)"
        self.plugin.projects.lookup = lambda cwd: (self.owner if cwd == "/work/billing" else None, self.names)

    def hook(self, **settings):
        ctx = Ctx(**settings)
        self.plugin.register(ctx)
        self.assertEqual(list(ctx.hooks), ["transform_session_title"])
        return ctx.hooks["transform_session_title"]

    def test_prefixes_a_project_session(self):
        self.assertEqual(self.hook()(title="Fix invoices", session_id="s", source="llm", cwd="/work/billing"),
                         "BS: Fix invoices")

    def test_settings_are_read_each_call(self):
        ctx = Ctx(uppercase=False)
        self.plugin.register(ctx)
        fn = ctx.hooks["transform_session_title"]
        self.assertEqual(fn(title="Fix invoices", cwd="/work/billing"), "bs: Fix invoices")
        ctx.settings["uppercase"] = True
        self.assertEqual(fn(title="Fix invoices", cwd="/work/billing"), "BS: Fix invoices")

    def test_no_cwd_or_no_project_returns_none(self):
        fn = self.hook()
        self.assertIsNone(fn(title="Fix invoices", cwd=""))
        self.assertIsNone(fn(title="Fix invoices", cwd="/elsewhere"))

    def test_already_correct_title_returns_none(self):
        self.assertIsNone(self.hook()(title="BS: Fix invoices", cwd="/work/billing"))

    def test_derive_missing_is_opt_in(self):
        self.owner = "Plain"
        self.assertIsNone(self.hook()(title="Fix invoices", cwd="/work/billing"))
        self.assertEqual(self.hook(derive_missing=True)(title="Fix invoices", cwd="/work/billing"), "PL: Fix invoices")

    def test_lookup_failure_leaves_the_title(self):
        def boom(cwd):
            raise RuntimeError("store locked")

        self.plugin.projects.lookup = boom
        self.assertIsNone(self.hook()(title="Fix invoices", cwd="/work/billing"))


if __name__ == "__main__":
    unittest.main()
