"""Deterministic index/source identity checks; never require GitHub or Android SDK."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

script = Path(__file__).resolve().parents[1] / "scripts" / "generate_store.py"
spec = importlib.util.spec_from_file_location("selura_store_generator", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CatalogTests(unittest.TestCase):
    def test_source_ids_stable_and_distinct(self):
        self.assertEqual(
            module.source_id("Selura NHentai", "en"),
            module.source_id("Selura NHentai", "en"),
        )
        self.assertNotEqual(module.source_id("Selura NHentai", "en"),
                            module.source_id("NHentai", "en"))
        self.assertNotEqual(module.source_id("Selura MangaDex", "en"),
                            module.source_id("MangaDex", "en"))
        self.assertEqual(len(module.MANGADEX_LANGUAGES),
                         len(set(module.MANGADEX_LANGUAGES)))

    def test_reject_missing_or_mismatched_apk(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            with self.assertRaisesRegex(ValueError, "Missing extension APK"):
                module.metadata(base / "not-an-apk.apk", "aapt", "apksigner")

    def test_generate_v2_json_index_and_legacy_redirect(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            for item in module.EXTENSIONS:
                with ZipFile(base / item["filename"], "w") as apk:
                    apk.writestr("res/icon.png", b"placeholder-icon")
            inputs = [
                {"package": ext["package"], "code": 104002 if index == 0 else 106003,
                 "name": "1.4.2" if index == 0 else "1.6.3",
                 "sha256": module.EXPECTED_CERT_SHA256}
                for index, ext in enumerate(module.EXTENSIONS)
            ]
            with patch.object(module, "metadata", side_effect=inputs):
                index = module.generate(base, base / "publish", "aapt", "apksigner")
            self.assertEqual(len(index["extensionList"]["extensions"]), 2)
            self.assertEqual(index["signingKey"],
                             module.EXPECTED_CERT_SHA256)
            listing = json.loads((base / "publish/index.json").read_text())
            self.assertEqual(listing["name"], "Selura Extensions")
            self.assertEqual(listing["signingKey"], module.EXPECTED_CERT_SHA256)
            self.assertEqual(len(listing["signingKey"]), 64)
            self.assertEqual(listing["extensionList"]["extensions"][0]["contentWarning"], "NSFW")
            self.assertEqual(listing["extensionList"]["extensions"][1]["contentWarning"], "MIXED")
            for entry in listing["extensionList"]["extensions"]:
                self.assertTrue(entry["resources"]["apkUrl"].startswith(module.RAW_BASE))
                self.assertTrue(entry["sources"])
                self.assertTrue(entry["versionCode"] > 0)
            redirect = json.loads((base / "publish/repo.json").read_text())
            self.assertEqual(redirect["index_v2"], module.RAW_BASE + "/index.json")
            self.assertEqual(redirect["meta"]["signingKeyFingerprint"], module.EXPECTED_CERT_SHA256)

    def test_reject_wrong_android_package(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            for item in module.EXTENSIONS:
                (base / item["filename"]).write_bytes(b"apk bytes placeholder")
            with patch.object(module, "metadata", return_value={
                "package": "untrusted.package", "code": 1, "name": "1.4.2",
                "sha256": module.EXPECTED_CERT_SHA256,
            }):
                with self.assertRaisesRegex(ValueError, "Wrong APK package"):
                    module.generate(base, base / "publish", "aapt", "apksigner")

    def test_reject_mixed_signing_certificates(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            for item in module.EXTENSIONS:
                (base / item["filename"]).write_bytes(b"apk bytes placeholder")
            with patch.object(module, "metadata", side_effect=[
                {"package": module.EXTENSIONS[0]["package"], "code": 1,
                 "name": "1.4.2", "sha256": "a" * 64},
                {"package": module.EXTENSIONS[1]["package"], "code": 2,
                 "name": "1.6.3", "sha256": "b" * 64},
            ]):
                with self.assertRaisesRegex(ValueError, "signer identities do not match"):
                    module.generate(base, base / "publish", "aapt", "apksigner")

    def test_sha256_fingerprint_required_not_sha1(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            for item in module.EXTENSIONS:
                (base / item["filename"]).write_bytes(b"placeholder APK")
            bad_digest = "1234567890abcdef1234567890abcdef12345678"  # 40-character SHA-1
            with patch.object(module, "metadata", side_effect=[
                {"package": item["package"], "code": 1, "name": "1.4.2", "sha256": bad_digest}
                for item in module.EXTENSIONS
            ]):
                with self.assertRaisesRegex(ValueError, "Unexpected signing certificate"):
                    module.generate(base, base / "publish", "aapt", "apksigner")


if __name__ == "__main__":
    unittest.main()
