# Seiryn extension security — live APK audit

## Why this was added

On the user's Android phone, Google Play Protect displayed "App scan recommended" when installing the independent Doujins extension, whereas a Keiyoushi extension did not display that prompt. The comparison does not establish maliciousness or prove why the system made that decision. Different app identities, signing keys, versions, installation modes and Play Protect reputation can affect Android's prompts.

The current Doujins APK identity is eu.kanade.tachiyomi.extension.en.seluradoujins, versionCode 109004. Its pinned Keiyoushi source Gradle declaration does not explicitly request permissions, but only inspection of the built APK can reveal the effective manifest permissions.

## Source inspection: how Seiryn installs APKs

The inherited native extension installer already supports multiple modes:

- Package Installer (default on most Android devices): submits the verified signed APK through the Android PackageInstaller service. Android and Play Protect retain authority to display security prompts.
- Legacy: starts Android's regular APK installer, which can show the same prompts.
- Private extension storage: copies and verifies the extension inside the reader's private directory instead of installing a separate Android application. This is an alternative feature architecture, NOT a Play Protect bypass or recommended substitute for malware scanning; do not silently switch users to it.
- Shizuku: an optional user-authorized privileged installer; not required for this investigation.

The reader checks the APK's signing key against the selected extension store before installing. That is useful, but independent of Google's malware/reputation evaluation.

## Verified first live run — October 24, 2026

The [first successful live APK audit run #2](https://github.com/zexaldragneel/selura-extensions/actions/runs/40093793170) **PASSED**:

- **43 of 43** APKs downloaded from the currently published store and independently verified with Android SDK tools.
- Original signing certificate, unique manifest package identity and published version matched on all 43.
- **341** catalog source IDs were preserved.
- **0** APKs requested any of the sensitive Android permissions explicitly tracked by the audit.
- **0** APKs failed identity or archive checks.
- All **28** store and security unit tests passed in the corresponding run.
- Full manifest permission lists, individual APK hashes and identity details are retained as workflow artifacts: [JSON/Markdown evidence](https://github.com/zexaldragneel/selura-extensions/actions/runs/40093793170/artifacts/12560192017).

The first draft of the checker failed because its certificate-text parser was too restrictive; it was corrected to accept the Android SDK apksigner output format already recognized by our publishing pipeline. That initial failure was not an actual invalid signature.

**Doujins is not requesting one of the monitored sensitive Android permissions in this release.** A Play Protect scan recommendation can still occur because independent packages and signing identities may be unfamiliar to Google's reputation system; this audit does not identify the definitive cause and does not suppress scans.

## Automated audit

The new Audit Published Extension APKs GitHub Actions workflow operates only on the current public store:

1. Confirms 43 unique extension packages, 341 source IDs and the existing trusted catalog certificate.
2. Downloads exactly the currently published public APK bytes, with no alternate mirrors.
3. Uses Android SDK aapt and apksigner to check every APK's signing certificate, package identity, installed version, valid ZIP structure and SHA-256 file digest.
4. Extracts every extension's AndroidManifest permissions and flags sensitive access such as SMS, contacts, call logs, microphone, camera, location, broad storage, overlays, accessibility and package installation.
5. Produces JSON and Markdown reports as workflow artifacts, and fails if sensitive permissions or integrity errors are found. Runs for related PRs, manually and weekly.

This is a static permissions and integrity audit, NOT a malware scan, certificate of safety or guarantee that Play Protect prompts disappear. Keep Play Protect enabled and choose Scan app when Android offers it.

## Data and identity preservation

This audit does not edit any existing APK, Android package name, APK signature, source ID, published repo branch, manga library, history, reading progress, downloaded chapter or backup. Any remediation involving an APK must be handled as a separate versioned, signed update with Android device acceptance.

See the Audit Published Extension APKs workflow summary and its two downloadable report artifacts for actual results; do not claim a passing full 43-APK audit until a complete workflow finishes.
