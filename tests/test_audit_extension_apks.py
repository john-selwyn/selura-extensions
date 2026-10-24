"""Offline tests for read-only real-APK audit. Uses no external services."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_extension_apks as audit
from generate_store import EXTENSIONS, EXPECTED_CERT_SHA256, RAW_BASE


def catalog():
    rows = []
    for i, spec in enumerate(EXTENSIONS):
        ids = range(299) if i == 0 else range(1)
        rows.append({
            "name": spec["name"], "packageName": spec["package"],
            "versionCode": 110000 + i,
            "sources": [{"id": str(j)} for j in ids],
            "resources": {"apkUrl": f"{RAW_BASE}/apk/{spec['filename']}"},
        })
    return {"signingKey": EXPECTED_CERT_SHA256, "extensionList": {"extensions": rows}}


class AuditTests(unittest.TestCase):
    def test_perms_extract_manifest_permissions_and_dedupe(self):
        raw = ("package: foo\n"
               "uses-permission: name='android.permission.INTERNET'\n"
               "uses-permission-sdk-23: name='android.permission.CAMERA'\n"
               "uses-permission: name='android.permission.INTERNET'\n")
        self.assertEqual(audit.parse_permissions(raw), [
            "android.permission.CAMERA", "android.permission.INTERNET",
        ])
        self.assertEqual(audit.parse_badging("package: name='com.own.ext' versionCode='109004' versionName='1.6.3'"),
                         ("com.own.ext", 109004))
        self.assertEqual(audit.parse_signers(f"Signer #1 certificate SHA-256 digest: {EXPECTED_CERT_SHA256}"),
                         [EXPECTED_CERT_SHA256])

    def test_reject_malicious_catalog_metadata_or_different_id(self):
        base = catalog()
        self.assertEqual(len(audit.checked_catalog(base)), 43)
        self.assertEqual(sum(len(r["sources"]) for r in base["extensionList"]["extensions"]), 341)
        manipulations = [
            ("signer", lambda b: b.update(signingKey="0" * 64)),
            ("unexpected mirror", lambda b: b["extensionList"]["extensions"][0]["resources"].update(apkUrl="https://evil.invalid/fake.apk")),
            ("wrong name", lambda b: b["extensionList"]["extensions"][0].update(name="newly swapped source")),
            ("wrong package", lambda b: b["extensionList"]["extensions"][0].update(packageName="com.evil.app")),
            ("wrong source count", lambda b: b["extensionList"]["extensions"][0]["sources"].pop()),
        ]
        for label, change in manipulations:
            with self.subTest(label=label):
                b = json.loads(json.dumps(base))
                change(b)
                with self.assertRaises(audit.AuditError):
                    audit.checked_catalog(b)

    def test_flags_permissions_even_when_other_identity_checks_pass(self):
        row = catalog()["extensionList"]["extensions"][0]
        spec = EXTENSIONS[0]
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            target = root / spec["filename"]
            with ZipFile(target, "w") as z:
                z.writestr("AndroidManifest.xml", b"Android binary manifest")
                z.writestr("classes.dex", b"stub")
            def tool(*argv):
                if "apksigner" in argv[0]:
                    return f"Signer #1 certificate SHA-256 digest: {EXPECTED_CERT_SHA256}\n"
                if "badging" in argv:
                    return f"package: name='{spec['package']}' versionCode='{row['versionCode']}' versionName='1.6.1'\n"
                if "permissions" in argv:
                    return ("uses-permission: name='android.permission.INTERNET'\n"
                            "uses-permission: name='android.permission.READ_SMS'\n")
                raise AssertionError(argv)
            with patch.object(audit, "command", side_effect=tool):
                actual = audit.audit_apk(spec, row, target, "aapt", "apksigner")
            self.assertEqual(actual["status"], "REVIEW")
            self.assertEqual(actual["sensitivePermissions"], ["android.permission.READ_SMS"])

    def test_reject_mismatched_signer_or_package(self):
        spec = EXTENSIONS[0]
        row = catalog()["extensionList"]["extensions"][0]
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / spec["filename"]
            with ZipFile(target, "w") as apk:
                apk.writestr("AndroidManifest.xml", b"manifest")
                apk.writestr("classes.dex", b"dex")
            for failure in ("bad signer", "bad pkg"):
                def tool(*args):
                    if "apksigner" in args[0]:
                        return f"Signer #1 certificate SHA-256 digest: {('a' * 64) if failure == 'bad signer' else EXPECTED_CERT_SHA256}\n"
                    if "badging" in args:
                        return f"package: name='com.wrong' versionCode='{row['versionCode']}'\n"
                    return ""
                with self.subTest(failure=failure), patch.object(audit, "command", side_effect=tool), self.assertRaises(audit.AuditError):
                    audit.audit_apk(spec, row, target, "aapt", "apksigner")

    def test_read_only_whole_catalog_report(self):
        index = catalog()
        with tempfile.TemporaryDirectory() as t:
            directory = Path(t)
            for spec in EXTENSIONS:
                with ZipFile(directory / spec["filename"], "w") as apk:
                    apk.writestr("AndroidManifest.xml", b"manifest")
                    apk.writestr("classes.dex", b"dex")
            package_version_by_file = {
                item["filename"]: (item["package"], 110000 + i)
                for i, item in enumerate(EXTENSIONS)
            }
            def tool(*args):
                if "apksigner" in args[0]:
                    return f"Signer #1 certificate SHA-256 digest: {EXPECTED_CERT_SHA256}\n"
                path = Path(args[-1]).name
                pkg, code = package_version_by_file[path]
                if "badging" in args:
                    return f"package: name='{pkg}' versionCode='{code}' versionName='1.6.3'\n"
                return "uses-permission: name='android.permission.INTERNET'\n"
            with patch.object(audit, "command", side_effect=tool):
                result = audit.run_audit(index, directory, "aapt", "apksigner")
            self.assertEqual(result["overall"], "PASS")
            self.assertEqual(result["verifiedAPKs"], 43)
            self.assertEqual(result["catalogSourceIDs"], 341)
            self.assertFalse(result["errors"])
            self.assertIn("Doujins", audit.as_markdown(result))
            self.assertIn("Google Play Protect", audit.as_markdown(result))


if __name__ == "__main__":
    unittest.main()
