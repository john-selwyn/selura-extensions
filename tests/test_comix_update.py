"""Regression checks for Comix.to-only safe extension catalog releases."""
import copy
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "scripts" / "validate_comix_update.py"
spec = importlib.util.spec_from_file_location("validate_comix_update", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ComixSafeUpdateTests(unittest.TestCase):
    def setUp(self):
        def entry(name, pkg, code, source_id):
            return {
                "name": name,
                "packageName": pkg,
                "versionCode": code,
                "versionName": f"1.6.{code}",
                "sources": [{"id": source_id, "name": name}],
                "resources": {"apkUrl": f"https://example.org/apk/{name}.apk"},
            }
        self.before = {
            "name": "Selura Extensions",
            "signingKey": "original-signer",
            "extensionList": {"extensions": [
                entry("Comix.to", module.COMIX_PACKAGE, 110001, 4121),
                entry("Existing", "eu.kanade.tachiyomi.extension.en.existing", 110001, 4122),
            ]},
        }
        self.after = copy.deepcopy(self.before)
        self.after["extensionList"]["extensions"][0]["versionCode"] = 110005
        self.after["extensionList"]["extensions"][0]["versionName"] = "1.6.4005"

    def test_only_comix_upgrade_is_accepted(self):
        module.validate_index(self.before, self.after, expected_count=2)

    def test_refuse_package_or_source_reassignment(self):
        for key, value in (("packageName", "wrong"), ("sources", [{"id": 111}])):
            modified = copy.deepcopy(self.after)
            modified["extensionList"]["extensions"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                module.validate_index(self.before, modified, expected_count=2)

    def test_refuse_unrelated_upgrade(self):
        modified = copy.deepcopy(self.after)
        modified["extensionList"]["extensions"][1]["versionCode"] += 1
        with self.assertRaises(ValueError):
            module.validate_index(self.before, modified, expected_count=2)

    def test_refuse_signature_changes_or_downgrade(self):
        modified = copy.deepcopy(self.after)
        modified["signingKey"] = "new-key"
        with self.assertRaises(ValueError):
            module.validate_index(self.before, modified, expected_count=2)
        modified = copy.deepcopy(self.after)
        modified["extensionList"]["extensions"][0]["versionCode"] = 110001
        with self.assertRaises(ValueError):
            module.validate_index(self.before, modified, expected_count=2)


if __name__ == "__main__":
    unittest.main()
