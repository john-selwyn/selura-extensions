#!/usr/bin/env python3
"""Fail-closed validation before publishing a Comix.to-only extension APK update.

Compare against the currently published repo branch. No historical package,
source ID, signature, or other extension may change in this maintenance release.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import urlparse

COMIX_PACKAGE = "eu.kanade.tachiyomi.extension.en.seluracomixto"


def validate_index(old: dict, new: dict, expected_count: int = 43) -> None:
    old_root = copy.deepcopy(old)
    new_root = copy.deepcopy(new)
    before = old_root["extensionList"].pop("extensions")
    after = new_root["extensionList"].pop("extensions")
    if old_root != new_root:
        raise ValueError("Repository identity, signer, endpoints, or catalog metadata changed")
    if len(before) != expected_count or len(after) != expected_count:
        raise ValueError("The existing extension inventory changed")
    original = {x["packageName"]: x for x in before}
    updated = {x["packageName"]: x for x in after}
    if len(original) != expected_count or set(original) != set(updated):
        raise ValueError("Duplicate/missing/new Android extension package")
    if COMIX_PACKAGE not in original:
        raise ValueError("Comix.to package identity was lost")
    seen_ids = set()
    for package, old_entry in original.items():
        new_entry = updated[package]
        if package == COMIX_PACKAGE:
            old_entry, new_entry = copy.deepcopy(old_entry), copy.deepcopy(new_entry)
            old_code = old_entry.pop("versionCode")
            new_code = new_entry.pop("versionCode")
            old_version = old_entry.pop("versionName")
            new_version = new_entry.pop("versionName")
            if new_code <= old_code or new_version == old_version:
                raise ValueError("Comix.to APK version did not increase")
            if old_entry != new_entry:
                raise ValueError("Comix.to package/source IDs/metadata changed")
        elif old_entry != new_entry:
            raise ValueError("Unrelated extension metadata changed: " + package)
        for src in updated[package]["sources"]:
            sid = str(src["id"])
            if sid in seen_ids:
                raise ValueError("Duplicate source ID: " + sid)
            seen_ids.add(sid)
    if expected_count == 43 and len(seen_ids) != 341:
        raise ValueError("Unexpected source ID inventory")


def validate_unchanged_apks(old: dict, apk_dir: Path, git_ref: str) -> None:
    for entry in old["extensionList"]["extensions"]:
        if entry["packageName"] == COMIX_PACKAGE:
            continue
        filename = Path(urlparse(entry["resources"]["apkUrl"]).path).name
        if not filename.endswith(".apk") or "/" in filename or filename.startswith("."):
            raise ValueError("Invalid original APK filename")
        old_bytes = subprocess.check_output(["git", "show", f"{git_ref}:apk/{filename}"])
        staged_file = apk_dir / filename
        if hashlib.sha256(old_bytes).digest() != hashlib.sha256(staged_file.read_bytes()).digest():
            raise ValueError("Published APK bytes unexpectedly changed: " + filename)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("previous_index", type=Path)
    p.add_argument("new_index", type=Path)
    p.add_argument("new_apk_dir", type=Path)
    p.add_argument("git_ref")
    a = p.parse_args()
    old = json.loads(a.previous_index.read_text(encoding="utf-8"))
    new = json.loads(a.new_index.read_text(encoding="utf-8"))
    validate_index(old, new)
    validate_unchanged_apks(old, a.new_apk_dir, a.git_ref)
    print("PASS: 43 packages, 341 source IDs, stable signer and 42 byte-identical previous APKs.")


if __name__ == "__main__":
    main()
