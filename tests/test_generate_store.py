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


    def test_orphaned_catalog_identity_is_stable_and_distinct(self):
        self.assertEqual(len(module.ORPHANED_EXTENSIONS), 18)
        self.assertEqual(len(module.EXTENSIONS), 38)
        self.assertEqual(module.ORPHANED_SOURCE_VERSION, 7301)
        self.assertEqual({item["name"] for item in module.ORPHANED_EXTENSIONS}, {
            "3Hentai", "AllPornComic", "Asura Scans", "Doujins", "Flame Comics",
            "HDoujin", "Hentai4Free", "HentaiHand", "HentaiRead", "Hiperdex",
            "Hive Scans", "MangaGeko", "Mangakakalot", "Mgread.io", "ToonGod",
            "Toonily", "Vortex Scans", "WebtoonXYZ",
        })
        self.assertEqual(len({item["package"] for item in module.EXTENSIONS}), 38)
        self.assertEqual(len({item["filename"] for item in module.EXTENSIONS}), 38)
        self.assertTrue(all(item["source_id_version"] == 7301
                            for item in module.ORPHANED_EXTENSIONS))
        self.assertEqual(
            module.alternate_orphan_id("seluramangageko", "734865402529567092"),
            module.alternate_orphan_id("seluramangageko", "734865402529567092"),
        )
        self.assertNotEqual(
            module.alternate_orphan_id("seluramangageko", "734865402529567092"),
            734865402529567092,
        )
        self.assertNotEqual(
            module.source_id("Asura Scans", "en", 7301),
            module.source_id("Asura Scans", "en", 1),
        )
        self.assertEqual(module.OWNER, "zexaldragneel")


    def test_12_new_sources_have_isolated_7302_identities(self):
        self.assertEqual(len(module.EXPANSION_EXTENSIONS), 12)
        self.assertEqual(module.EXPANSION_SOURCE_VERSION, 7302)
        self.assertEqual({item["name"] for item in module.EXPANSION_EXTENSIONS}, {
            "Comick (Unoriginal)", "GlobalComix", "MangaToon (Limited)",
            "Manga UP!", "MANGA Plus Creators by SHUEISHA", "NamiComi",
            "Dynasty Scans", "Gunnerkrigg Court", "Mangago", "Mangahere",
            "MangaFox", "Manganato",
        })
        self.assertEqual(len(module.BASE_EXTENSIONS), 8)
        self.assertEqual(len(module.ORPHANED_EXTENSIONS), 18)
        self.assertEqual(len(module.EXTENSIONS), 38)
        self.assertEqual(len(module.EXPANSION_EXTENSIONS[1]["languages"]), 41)
        self.assertEqual(len(module.EXPANSION_EXTENSIONS[5]["languages"]), 43)
        self.assertTrue(all(item["source_id_version"] == 7302
                            for item in module.EXPANSION_EXTENSIONS))
        self.assertNotEqual(
            module.alternate_expansion_id("seluramangahere", "2"), 2)
        self.assertEqual(
            module.alternate_expansion_id("seluracomicklive", "4972933717624256217"),
            module.alternate_expansion_id("seluracomicklive", "4972933717624256217"),
        )
        self.assertNotEqual(
            module.source_id("Mangago", "en", 7302),
            module.source_id("Mangago", "en", 1),
        )
        self.assertEqual(len({it["package"] for it in module.EXTENSIONS}), 38)
        self.assertEqual(len({it["filename"] for it in module.EXTENSIONS}), 38)

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
            self.assertEqual(len(index["extensionList"]["extensions"]), 38)
            self.assertEqual(index["signingKey"],
                             module.EXPECTED_CERT_SHA256)
            listing = json.loads((base / "publish/index.json").read_text())
            self.assertEqual(listing["name"], "Selura Extensions")
            self.assertEqual(listing["signingKey"], module.EXPECTED_CERT_SHA256)
            self.assertEqual(len(listing["signingKey"]), 64)
            self.assertEqual(listing["extensionList"]["extensions"][0]["contentWarning"], "NSFW")
            self.assertEqual(listing["extensionList"]["extensions"][0]["name"], "NHentai")
            self.assertEqual(listing["extensionList"]["extensions"][1]["name"], "MangaDex")
            self.assertEqual(
                listing["extensionList"]["extensions"][0]["sources"][0]["id"],
                module.source_id("Selura NHentai", "all"),
            )
            self.assertEqual(
                listing["extensionList"]["extensions"][1]["sources"][0]["id"],
                module.source_id("Selura MangaDex", module.MANGADEX_LANGUAGES[0]),
            )
            self.assertTrue(all(not e["name"].startswith("Selura ") for e in listing["extensionList"]["extensions"]))
            self.assertEqual(len({e["packageName"] for e in listing["extensionList"]["extensions"]}), 38)
            self.assertEqual(
                listing["extensionList"]["extensions"][2]["sources"][0]["id"],
                module.source_id("MANGA Plus by SHUEISHA", "en", 2),
            )
            self.assertEqual(listing["extensionList"]["extensions"][1]["contentWarning"], "MIXED")
            self.assertEqual(len(listing["extensionList"]["extensions"]), 38)
            by_name = {entry["name"]: entry for entry in listing["extensionList"]["extensions"]}
            self.assertEqual(
                by_name["Flame Comics"]["sources"][0]["id"],
                module.alternate_orphan_id("seluraflamecomics", "8531542650987673943"),
            )
            self.assertEqual(
                next(source["id"] for source in by_name["3Hentai"]["sources"]
                     if source["language"] == "pl"),
                module.alternate_orphan_id("selurahentai3", "7940950215101782907"),
            )
            self.assertEqual(
                next(source["id"] for source in by_name["HentaiHand"]["sources"]
                     if source["language"] == "pt-BR"),
                module.alternate_orphan_id("selurahentaihand", "2516244587139644000"),
            )
            self.assertEqual(
                by_name["Asura Scans"]["sources"][0]["id"],
                module.source_id("Asura Scans", "en", 7301),
            )
            self.assertEqual(by_name["MangaDex"]["packageName"],
                             "eu.kanade.tachiyomi.extension.all.seluramangadex")
            self.assertEqual(by_name["NHentai"]["packageName"],
                             "eu.kanade.tachiyomi.extension.all.seluranhentai")
            self.assertEqual(
                by_name["Comick (Unoriginal)"]["sources"][0]["id"],
                module.alternate_expansion_id("seluracomicklive", "4972933717624256217"),
            )
            self.assertEqual(
                next(src["id"] for src in by_name["GlobalComix"]["sources"]
                     if src["language"] == "sq"),
                module.alternate_expansion_id("seluraglobalcomix", "3356591153022230079"),
            )
            self.assertEqual(
                next(src["id"] for src in by_name["MangaToon (Limited)"]["sources"]
                     if src["language"] == "pt-BR"),
                module.alternate_expansion_id("seluramangatoon", "2064722193112934135"),
            )
            self.assertEqual(
                by_name["Mangahere"]["sources"][0]["id"],
                module.alternate_expansion_id("seluramangahere", "2"),
            )
            self.assertEqual(
                by_name["Mangago"]["sources"][0]["id"],
                module.source_id("Mangago", "en", 7302),
            )
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
                {"package": ext["package"], "code": i+1,
                 "name": "1.6.3", "sha256": ("b" if i == 1 else "a") * 64}
                for i, ext in enumerate(module.EXTENSIONS)
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
