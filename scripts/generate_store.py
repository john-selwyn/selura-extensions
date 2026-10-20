#!/usr/bin/env python3
"""Publish a Mihon/Selura-compatible JSON extension store from verified signed APKs.

No private repository credentials or signing keys are read by this program.
Input APKs are supplied by the GitHub Actions workflow with read-only access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from zipfile import ZipFile

OWNER = "zexaldragneel"
REPOSITORY = "selura-extensions"
RAW_BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPOSITORY}/repo"
SITE_URL = f"https://github.com/{OWNER}/{REPOSITORY}"
EXPECTED_CERT_SHA256 = "da9cfd25f9b1c694b585d427e5faa8c9a1d052b8d846051fbe1569d65c851d42"

# Exact source language declarations from pinned Keiyoushi MangaDex Gradle source.
MANGADEX_LANGUAGES = (
    "af", "sq", "ar", "az", "eu", "be", "bn", "bg", "my", "ca", "zh-Hans", "zh-Hant",
    "cv", "hr", "cs", "da", "nl", "en", "eo", "et", "fil", "fi", "fr", "ka", "de",
    "el", "he", "hi", "hu", "ga", "id", "it", "ja", "jv", "kk", "ko", "la", "lt",
    "ms", "mn", "ne", "no", "fa", "pl", "pt-BR", "pt", "ro", "ru", "sr", "sk",
    "es-419", "es", "sv", "ta", "te", "th", "tr", "uk", "ur", "uz", "vi",
)
NHENTAI_LANGUAGES = ("all", "en", "ja", "zh")
# Natural store listing titles. The first two preserve the existing source
# IDs based on their original "Selura ..." name, so old manga still open.
BASE_EXTENSIONS = (
    {
        "filename": "selura-nhentai.apk",
        "name": "NHentai",
        "source_id_name": "Selura NHentai",
        "source_id_version": 1,
        "package": "eu.kanade.tachiyomi.extension.all.seluranhentai",
        "url": "https://nhentai.net",
        "warning": "NSFW",
        "languages": NHENTAI_LANGUAGES,
    },
    {
        "filename": "selura-mangadex.apk",
        "name": "MangaDex",
        "source_id_name": "Selura MangaDex",
        "source_id_version": 1,
        "package": "eu.kanade.tachiyomi.extension.all.seluramangadex",
        "url": "https://mangadex.org",
        "warning": "MIXED",
        "languages": MANGADEX_LANGUAGES,
    },
    {
        "filename": "seluramangaplus.apk",
        "name": "MANGA Plus by SHUEISHA",
        "source_id_version": 2,
        "package": "eu.kanade.tachiyomi.extension.all.seluramangaplus",
        "url": "https://mangaplus.shueisha.co.jp",
        "warning": "SAFE",
        "languages": ("en", "es", "fr", "id", "pt-BR", "ru", "th", "vi", "de"),
    },
    {
        "filename": "selurawebtoons.apk",
        "name": "Webtoons.com",
        "source_id_version": 2,
        "package": "eu.kanade.tachiyomi.extension.all.selurawebtoons",
        "url": "https://www.webtoons.com",
        "warning": "SAFE",
        "languages": ("en", "id", "th", "es", "fr", "zh-Hant", "de"),
    },
    {
        "filename": "seluramangafire.apk",
        "name": "MangaFire",
        "source_id_version": 2,
        "package": "eu.kanade.tachiyomi.extension.all.seluramangafire",
        "url": "https://mangafire.to",
        "warning": "MIXED",
        "languages": ("en", "es", "es-419", "fr", "ja", "pt", "pt-BR"),
    },
    {
        "filename": "seluramangapill.apk",
        "name": "MangaPill",
        "source_id_version": 2,
        "package": "eu.kanade.tachiyomi.extension.en.seluramangapill",
        "url": "https://mangapill.com",
        "warning": "MIXED",
        "languages": ("en",),
    },
    {
        "filename": "seluramangakatana.apk",
        "name": "MangaKatana",
        "source_id_version": 2,
        "package": "eu.kanade.tachiyomi.extension.en.seluramangakatana",
        "url": "https://mangakatana.com",
        "warning": "MIXED",
        "languages": ("en",),
    },
    {
        "filename": "seluramangabat.apk",
        "name": "Mangabat",
        "source_id_version": 2,
        "package": "eu.kanade.tachiyomi.extension.en.seluramangabat",
        "url": "https://www.mangabats.com",
        "warning": "MIXED",
        "languages": ("en",),
    },
)


# Pinned, CI-verified release: test-orphaned-18-pr-29-run-4.
# Immutable source identity family versionId=7301, distinct from existing
# original/Keiyoushi library entries. Historical explicit IDs use the same
# stable SHA-256 remap as selura-reader/selura_extensions/orphaned_sources.py.
ORPHANED_SOURCE_VERSION = 7301
ORPHANED_EXTENSIONS = (
    {
        "filename": "selurahentai3.apk",
        "name": "3Hentai",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.all.selurahentai3",
        "url": "https://3hentai.net",
        "warning": "NSFW",
        "languages": ("all", "en", "ja", "ko", "zh", "mo", "es", "pt", "id", "jv", "tl", "vi", "th", "my", "tr", "ru", "uk", "pl", "fi", "de", "it", "fr", "nl", "cs", "hu", "bg", "is", "la", "ar"),
        "explicit_old_ids": {"pl": "7940950215101782907"},
    },
    {
        "filename": "seluraallporncomic.apk",
        "name": "AllPornComic",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluraallporncomic",
        "url": "https://allporncomic.com",
        "warning": "NSFW",
        "languages": ("en",),
    },
    {
        "filename": "seluraasurascans.apk",
        "name": "Asura Scans",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluraasurascans",
        "url": "https://asurascans.com",
        "warning": "SAFE",
        "languages": ("en",),
    },
    {
        "filename": "seluradoujins.apk",
        "name": "Doujins",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluradoujins",
        "url": "https://doujins.com",
        "warning": "NSFW",
        "languages": ("en",),
    },
    {
        "filename": "seluraflamecomics.apk",
        "name": "Flame Comics",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluraflamecomics",
        "url": "https://flamecomics.xyz",
        "warning": "SAFE",
        "languages": ("en",),
        "explicit_old_ids": {"en": "8531542650987673943"},
    },
    {
        "filename": "selurahdoujin.apk",
        "name": "HDoujin",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.all.selurahdoujin",
        "url": "https://hdoujin.org",
        "warning": "NSFW",
        "languages": ("all", "en", "es", "ja", "ko", "zh"),
        "explicit_old_ids": {"ko": "8377507648400729012"},
    },
    {
        "filename": "selurahentai4free.apk",
        "name": "Hentai4Free",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.selurahentai4free",
        "url": "https://hentai4free.net",
        "warning": "NSFW",
        "languages": ("en",),
    },
    {
        "filename": "selurahentaihand.apk",
        "name": "HentaiHand",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.all.selurahentaihand",
        "url": "https://hentaihand.com",
        "warning": "NSFW",
        "languages": ("all", "ja", "en", "zh", "bg", "ceb", "other", "tl", "ar", "el", "sr", "jv", "uk", "tr", "fi", "la", "mn", "eo", "sk", "cs", "ko", "ru", "it", "es", "pt-BR", "th", "fr", "id", "vi", "de", "pl", "hu", "nl", "hi"),
        "explicit_old_ids": {"all": "1235047015955289468", "other": "7302549142935671434", "pt-BR": "2516244587139644000"},
    },
    {
        "filename": "selurahentairead.apk",
        "name": "HentaiRead",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.selurahentairead",
        "url": "https://hentairead.com",
        "warning": "NSFW",
        "languages": ("en",),
    },
    {
        "filename": "selurahiperdex.apk",
        "name": "Hiperdex",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.selurahiperdex",
        "url": "https://hiperdex.tv",
        "warning": "MIXED",
        "languages": ("en",),
    },
    {
        "filename": "selurahivescans.apk",
        "name": "Hive Scans",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.selurahivescans",
        "url": "https://hivetoons.org",
        "warning": "SAFE",
        "languages": ("en",),
    },
    {
        "filename": "seluramangageko.apk",
        "name": "MangaGeko",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluramangageko",
        "url": "https://www.mgeko.cc",
        "warning": "MIXED",
        "languages": ("en",),
        "explicit_old_ids": {"en": "734865402529567092"},
    },
    {
        "filename": "seluramangakakalot.apk",
        "name": "Mangakakalot",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluramangakakalot",
        "url": "https://www.mangakakalot.gg",
        "warning": "MIXED",
        "languages": ("en",),
    },
    {
        "filename": "seluramgreadio.apk",
        "name": "Mgread.io",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluramgreadio",
        "url": "https://mgread.io",
        "warning": "MIXED",
        "languages": ("en",),
    },
    {
        "filename": "seluratoongod.apk",
        "name": "ToonGod",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluratoongod",
        "url": "https://www.toongod.org",
        "warning": "MIXED",
        "languages": ("en",),
    },
    {
        "filename": "seluratoonily.apk",
        "name": "Toonily",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluratoonily",
        "url": "https://toonily.com",
        "warning": "MIXED",
        "languages": ("en",),
    },
    {
        "filename": "seluravortexscans.apk",
        "name": "Vortex Scans",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.seluravortexscans",
        "url": "https://vortexscans.org",
        "warning": "SAFE",
        "languages": ("en",),
    },
    {
        "filename": "selurawebtoonxyz.apk",
        "name": "WebtoonXYZ",
        "source_id_version": ORPHANED_SOURCE_VERSION,
        "package": "eu.kanade.tachiyomi.extension.en.selurawebtoonxyz",
        "url": "https://www.webtoon.xyz",
        "warning": "MIXED",
        "languages": ("en",),
    },
)
EXTENSIONS = BASE_EXTENSIONS + ORPHANED_EXTENSIONS


def alternate_orphan_id(package_suffix: str, old_id: str) -> int:
    """Mirror the immutable remap already used in the built extension modules."""
    seed = ("selura-orphaned-v1:" + package_suffix + ":" + old_id).encode("utf-8")
    return (int.from_bytes(hashlib.sha256(seed).digest()[:8], "big") & ((1 << 63) - 1)) or 1




def source_id(name: str, language: str, version_id: int = 1) -> int:
    """Match Keiyoushi's Java MD5-derived source ID algorithm exactly."""
    key = f"{name.lower()}/{language}/{version_id}".encode("utf-8")
    return int.from_bytes(hashlib.md5(key).digest()[:8], "big") & ((1 << 63) - 1)


def run(command: list[str]) -> str:
    return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT)


def metadata(apk: Path, aapt: str, apksigner: str) -> dict:
    if not apk.is_file() or apk.stat().st_size == 0:
        raise ValueError(f"Missing extension APK: {apk}")
    badging = run([aapt, "dump", "badging", str(apk)])
    m = re.search(
        r"(?m)^package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'",
        badging,
    )
    if m is None:
        raise ValueError(f"No Android package/versions in {apk}")
    signature = run([apksigner, "verify", "--verbose", "--print-certs", str(apk)])
    def digest(kind: str) -> str:
        found = re.search(
            rf"certificate SHA-{kind} digest: ([a-fA-F0-9]+)", signature,
        )
        if not found:
            raise ValueError(f"APK missing SHA-{kind} signing certificate fingerprint")
        return found.group(1).lower()

    sha256 = digest("256")
    if sha256 != EXPECTED_CERT_SHA256:
        raise ValueError(f"Unexpected signer on {apk.name}: {sha256}")
    return {
        "package": m.group(1),
        "code": int(m.group(2)),
        "name": m.group(3),
        "sha256": sha256,
    }


def generate(input_dir: Path, output_dir: Path, aapt: str, apksigner: str) -> dict:
    # Prepare all metadata BEFORE publishing anything; fail closed on mismatch.
    apk_metadata = {}
    for spec in EXTENSIONS:
        apk = input_dir / spec["filename"]
        info = metadata(apk, aapt, apksigner)
        if info["package"] != spec["package"]:
            raise ValueError(f"Wrong APK package for {spec['name']}: {info['package']}")
        if info["code"] <= 0 or not re.fullmatch(r"\d+\.\d+\.\d+", info["name"]):
            raise ValueError(f"Unexpected Android version for {spec['name']}")
        apk_metadata[spec["filename"]] = info

    # Mihon ExtensionLoader.getSignatures compares SHA-256 (not SHA-1).
    signers = {item["sha256"] for item in apk_metadata.values()}
    if len(signers) != 1:
        raise ValueError("Extension APK signer identities do not match")
    signer_sha256 = signers.pop()
    if signer_sha256 != EXPECTED_CERT_SHA256:
        raise ValueError("Unexpected signing certificate for Selura extension store")

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "apk").mkdir(exist_ok=True)
    (output_dir / "icon").mkdir(exist_ok=True)
    extensions = []

    for spec in EXTENSIONS:
        filename = spec["filename"]
        info = apk_metadata[filename]
        shutil.copy2(input_dir / filename, output_dir / "apk" / filename)
        icon_name = filename.removesuffix(".apk") + ".png"
        # Source extension APK contains the actual upstream vector-generated
        # 192px icon resource under an obfuscated, but stable, resource path.
        with ZipFile(input_dir / filename) as archive:
            icons = [
                item for item in archive.infolist()
                if item.filename.startswith("res/") and item.filename.endswith(".png")
                and item.file_size > 0
            ]
            if not icons:
                raise ValueError(f"No extension icon found in {filename}")
            largest = max(icons, key=lambda item: item.file_size)
            (output_dir / "icon" / icon_name).write_bytes(archive.read(largest))
        lib_version = info["name"].rsplit(".", 1)[0]
        extensions.append(
            {
                "name": spec["name"],
                "packageName": spec["package"],
                "resources": {
                    "apkUrl": f"{RAW_BASE}/apk/{filename}",
                    "iconUrl": f"{RAW_BASE}/icon/{icon_name}",
                },
                "extensionLib": lib_version,
                "versionCode": info["code"],
                "versionName": info["name"],
                "contentWarning": spec["warning"],
                "sources": [
                    {
                        "id": (
                            alternate_orphan_id(
                                spec["package"].rsplit(".", 1)[-1],
                                spec["explicit_old_ids"][language],
                            )
                            if language in spec.get("explicit_old_ids", {})
                            else source_id(
                                spec.get("source_id_name", spec["name"]),
                                language,
                                spec["source_id_version"],
                            )
                        ),
                        "name": spec["name"],
                        "language": language,
                        "homeUrl": spec["url"],
                        "mirrorUrls": [],
                        "message": None,
                    }
                    for language in spec["languages"]
                ],
            }
        )
    index = {
        "name": "Selura Extensions",
        "badgeLabel": "Selura",
        "signingKey": signer_sha256,
        "contact": {"website": SITE_URL, "discord": None},
        "extensionList": {"extensions": extensions},
        "extensionListUrl": None,
    }
    legacy = {
        "index_v2": f"{RAW_BASE}/index.json",
        "meta": {
            "name": "Selura Extensions",
            "shortName": "Selura",
            "website": SITE_URL,
            "signingKeyFingerprint": signer_sha256,
        },
    }
    (output_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    (output_dir / "repo.json").write_text(
        json.dumps(legacy, indent=2) + "\n", encoding="utf-8",
    )
    return index


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apk-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--aapt", required=True)
    p.add_argument("--apksigner", required=True)
    args = p.parse_args()
    index = generate(args.apk_dir, args.output_dir, args.aapt, args.apksigner)
    print(f"Generated Selura store with {len(index['extensionList']['extensions'])} signed extensions")


if __name__ == "__main__":
    main()
