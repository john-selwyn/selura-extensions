#!/usr/bin/env python3
"""Read-only static audit of EXACT APK bytes published in the Selura store.

Inspects signed archive identity, manifest permissions and manifest metadata.
A clean static report is NOT a malware verdict or a Play Protect exemption.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZipFile, BadZipFile

from generate_store import EXTENSIONS, EXPECTED_CERT_SHA256, RAW_BASE

# Permissions not needed for remotely fetched comic sources; investigate
# before distributing any APK that requests one. No Play Protect bypass.
SENSITIVE_PERMISSIONS = frozenset({
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS",
    "android.permission.READ_CALL_LOG",
    "android.permission.WRITE_CALL_LOG",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.ACCESS_BACKGROUND_LOCATION",
    "android.permission.READ_PHONE_STATE",
    "android.permission.CALL_PHONE",
    "android.permission.READ_CALENDAR",
    "android.permission.WRITE_CALENDAR",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.MANAGE_EXTERNAL_STORAGE",
    "android.permission.QUERY_ALL_PACKAGES",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.WRITE_SETTINGS",
    "android.permission.PACKAGE_USAGE_STATS",
    "android.permission.BIND_ACCESSIBILITY_SERVICE",
    "android.permission.BIND_VPN_SERVICE",
    "android.permission.BIND_DEVICE_ADMIN",
    "android.permission.READ_MEDIA_IMAGES",
    "android.permission.READ_MEDIA_VIDEO",
    "android.permission.READ_MEDIA_AUDIO",
})

# Other declared permissions still appear in the report for human review.
PERMISSION_RE = re.compile(r"(?m)^\s*uses-permission(?:-sdk-\d+)?:\s*name='([^']+)'")
PACKAGE_RE = re.compile(r"^package:\s+name='([^']+)'\s+versionCode='(\d+)'", re.MULTILINE)
CERT_RE = re.compile(r"(?mi)^Signer #\d+ certificate SHA-256 digest:\s*([a-f0-9]{64})\s*$")
APK_LIMIT_BYTES = 20 * 1024 * 1024


class AuditError(ValueError):
    pass


def command(*args: str) -> str:
    result = subprocess.run(
        list(args), check=True, capture_output=True, text=True, timeout=35,
    )
    return result.stdout + "\n" + result.stderr


def parse_badging(output: str) -> tuple[str, int]:
    match = PACKAGE_RE.search(output)
    if not match:
        raise AuditError("aapt produced no readable package/version identity")
    return match.group(1), int(match.group(2))


def parse_signers(output: str) -> list[str]:
    signers = CERT_RE.findall(output)
    if not signers:
        raise AuditError("apksigner produced no verifiable SHA-256 certificate")
    return signers


def parse_permissions(output: str) -> list[str]:
    return sorted(set(PERMISSION_RE.findall(output)))


def checked_catalog(index: dict) -> list[tuple[dict, dict]]:
    rows = index.get("extensionList", {}).get("extensions", [])
    specs = {e["package"]: e for e in EXTENSIONS}
    if len(rows) != len(specs) or len(specs) != 43:
        raise AuditError("Live catalog differs from 43 pinned extension contracts")
    if len({r.get("packageName") for r in rows}) != 43:
        raise AuditError("Duplicate or missing Android package identity in live catalog")
    if sum(len(r.get("sources", [])) for r in rows) != 341:
        raise AuditError("Live catalog source identity count changed from 341")
    if index.get("signingKey") != EXPECTED_CERT_SHA256:
        raise AuditError("Live catalog signing key differs from verified signer")
    pairs = []
    for row in rows:
        package = row.get("packageName")
        spec = specs.get(package)
        if spec is None or row.get("name") != spec["name"]:
            raise AuditError(f"Unexpected catalog extension: {package}")
        expected_url = f"{RAW_BASE}/apk/{spec['filename']}"
        if row.get("resources", {}).get("apkUrl") != expected_url:
            raise AuditError(f"Unexpected APK distribution origin: {package}")
        if not isinstance(row.get("versionCode"), int) or row["versionCode"] < 1:
            raise AuditError(f"Missing versionCode: {package}")
        if not row.get("sources"):
            raise AuditError(f"Missing source IDs: {package}")
        pairs.append((spec, row))
    return pairs


def audit_apk(spec: dict, row: dict, path: Path, aapt: str, apksigner: str) -> dict:
    if not path.is_file() or not 100 < path.stat().st_size <= APK_LIMIT_BYTES:
        raise AuditError(f"Missing/unexpected APK size: {spec['filename']}")
    try:
        with ZipFile(path) as archive:
            files = set(archive.namelist())
            if "AndroidManifest.xml" not in files or not any(re.fullmatch(r"classes\d*\.dex", name) for name in files):
                raise AuditError(f"Missing executable APK contents: {spec['filename']}")
    except BadZipFile as exc:
        raise AuditError(f"Corrupt published APK: {spec['filename']}") from exc
    signer_output = command(apksigner, "verify", "--print-certs", str(path))
    signers = parse_signers(signer_output)
    if len(signers) != 1 or signers[0] != EXPECTED_CERT_SHA256:
        raise AuditError(f"Wrong or multiple signing certificates: {spec['filename']}")
    package, version = parse_badging(command(aapt, "dump", "badging", str(path)))
    if package != spec["package"] or version != row["versionCode"]:
        raise AuditError(f"Package/version mismatch in {spec['filename']}: {package}/{version}")
    permissions = parse_permissions(command(aapt, "dump", "permissions", str(path)))
    sensitive = sorted(set(permissions) & SENSITIVE_PERMISSIONS)
    return {
        "name": spec["name"], "package": package, "versionCode": version,
        "apk": spec["filename"], "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "signerSha256": signers[0], "permissions": permissions,
        "sensitivePermissions": sensitive, "status": "REVIEW" if sensitive else "PASS",
    }


def run_audit(index: dict, apk_dir: Path, aapt: str, apksigner: str) -> dict:
    pairs = checked_catalog(index)
    results = []
    # Continue auditing after an individual APK problem; report all offenders.
    errors = []
    for spec, row in pairs:
        try:
            results.append(audit_apk(spec, row, apk_dir / spec["filename"], aapt, apksigner))
        except (AuditError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            errors.append(f"{spec['filename']}: {exc}")
    flagged = [r for r in results if r["sensitivePermissions"]]
    return {
        "scope": "read-only audit of 43 public extension APKs, no replacements or installs",
        "catalogPackages": len(pairs),
        "catalogSourceIDs": sum(len(x[1]["sources"]) for x in pairs),
        "verifiedAPKs": len(results),
        "sensitivePermissionPackages": len(flagged),
        "errors": errors,
        "overall": "PASS" if len(results) == 43 and not flagged and not errors else "REVIEW",
        "extensions": results,
        "limitations": (
            "Static manifest/signing inspection cannot establish malware-free behavior, "
            "Google Play Protect reputation, or whether a future scan prompt appears."
        ),
    }


def as_markdown(audit: dict) -> str:
    lines = [
        "# Seiryn published extension APK security audit",
        "",
        f"**Result: {audit['overall']}** — verified {audit['verifiedAPKs']}/43 signed APKs; "
        f"{audit['sensitivePermissionPackages']} APKs request listed sensitive permissions. "
        "Store source identities: 341.",
        "",
        "This report audits the **actual public APK bytes**, not just repository source or generated metadata. "
        "A clean result does not imply Google Play Protect recognition or malware-free behavior.",
        "",
        "| Extension | Manifest permissions | Review |",
        "|---|---|---|",
    ]
    for r in audit["extensions"]:
        perms = ", ".join(r["permissions"]) if r["permissions"] else "None declared"
        lines.append(f"| {r['name']} | {perms} | {r['status']} |")
    if audit["errors"]:
        lines.extend(["", "## Failed verification", *[f"- {e}" for e in audit["errors"]]])
    lines.extend([
        "",
        "## Play Protect note",
        "",
        "Independently named/signed extension packages may not yet be recognized by Play Protect. "
        "A security scan recommendation is not a malware verdict. No code in this audit "
        "disables Play Protect or hides Android's package installer. "
        "Use the system scan when offered.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--apk-dir", required=True, type=Path)
    parser.add_argument("--aapt", required=True)
    parser.add_argument("--apksigner", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = run_audit(
        json.loads(args.catalog.read_text(encoding="utf-8")),
        args.apk_dir, args.aapt, args.apksigner,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "extension_apk_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output_dir / "extension_apk_audit.md").write_text(as_markdown(report) + "\n")
    print(
        f"{report['overall']}: {report['verifiedAPKs']}/43 verified, "
        f"{report['sensitivePermissionPackages']} needing permission review, "
        f"{len(report['errors'])} failures"
    )
    for entry in report["extensions"]:
        if entry["sensitivePermissions"]:
            print(f"REVIEW {entry['name']}: {', '.join(entry['sensitivePermissions'])}")
    for error in report["errors"]:
        print(f"ERROR {error}")
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
