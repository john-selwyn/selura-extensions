"""Hive Scans-only store release invariant tests."""
import copy
import importlib.util
from pathlib import Path
import unittest

script = Path(__file__).resolve().parents[1] / "scripts" / "validate_hivescans_update.py"
spec = importlib.util.spec_from_file_location("validate_hivescans_update", script)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class HiveUpdateTests(unittest.TestCase):
    def setUp(self):
        def item(name, pkg, code, source_id):
            return {
                "name": name, "packageName": pkg,
                "versionCode": code, "versionName": f"1.6.{code}",
                "sources": [{"id": source_id, "name": name}],
                "resources": {
                    "apkUrl": f"https://example.org/apk/{name}.apk",
                    "iconUrl": f"https://example.org/icon/{name}.png",
                },
            }
        self.old = {
            "signingKey": "unchanged",
            "extensionList": {"extensions": [
                item("hive", guard.TARGET, 109031, 123),
                item("other", "eu.kanade.tachiyomi.extension.en.other", 109031, 456),
            ]},
        }
        self.new = copy.deepcopy(self.old)
        self.new["extensionList"]["extensions"][0]["versionCode"] = 110001
        self.new["extensionList"]["extensions"][0]["versionName"] = "1.6.4001"

    def verify(self, after):
        guard.compare_catalog(self.old, after, expected_count=2, expected_sources=2)

    def test_hive_upgrade_only(self):
        self.verify(self.new)

    def test_no_downgrade_or_same_version(self):
        modified = copy.deepcopy(self.new)
        modified["extensionList"]["extensions"][0]["versionCode"] = 109031
        with self.assertRaises(ValueError):
            self.verify(modified)

    def test_no_source_or_package_reassignment(self):
        for key, value in (("sources", [{"id": 999}]), ("packageName", "changed")):
            modified = copy.deepcopy(self.new)
            modified["extensionList"]["extensions"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.verify(modified)

    def test_no_other_change_or_signer(self):
        modified = copy.deepcopy(self.new)
        modified["extensionList"]["extensions"][1]["name"] = "renamed"
        with self.assertRaises(ValueError):
            self.verify(modified)
        modified = copy.deepcopy(self.new)
        modified["signingKey"] = "other signer"
        with self.assertRaises(ValueError):
            self.verify(modified)


if __name__ == "__main__":
    unittest.main()
