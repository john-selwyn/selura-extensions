# Selura Extension Store — Maintenance

## Repositories

- **Android reader and signed source builds:** [zexaldragneel/selura-reader](https://github.com/zexaldragneel/selura-reader), including source-extension PRs #25–#29.
- **Public extension catalog and publication:** [zexaldragneel/selura-extensions](https://github.com/zexaldragneel/selura-extensions).
- **Stable catalog endpoint:** `https://raw.githubusercontent.com/zexaldragneel/selura-extensions/repo/repo.json`.
- **Generated store:** `repo` branch containing `repo.json`, `index.json`, `apk/` and `icon/`.

Both repositories are public. **No personal-access token is needed** for the publisher to read already-public release APKs: use the automatic GitHub Actions `github.token` for read-only public release download. Never put a personal token into source code, workflows, issues, PR text or chat; rotate unused older tokens through GitHub settings. Signing keys stay confined to the reader build workflow.

## Signed source releases

The publisher retrieves pinned **immutable** APK release tags from the reader repository:

| Source batch | Verified release |
| --- | --- |
| Original NHentai | `test-selura-source-pr-25-run-12` |
| Original MangaDex | `test-selura-mangadex-pr-26-run-3` |
| Six established extensions | `test-selura-batch-pr-28-run-6` |
| 18 orphaned extensions (excluding NHentai) | `test-orphaned-18-pr-29-run-4` |

Never change the current original APK identities, already-published source IDs or signing certificate during catalog updates. Existing 8 source packages remain byte-identical to their pinned releases; the 18 new source packages use their own fixed source ID family and package names. Physical device confirmation of the new sources remains an acceptance gate.

## Publishing process

1. Make changes to `scripts/generate_store.py`, corresponding tests and the pinned releases in `.github/workflows/publish-store.yml` on a feature branch.
2. Run the pull-request CI tests; reject missing or incorrectly signed APKs, wrong manifest package identities, duplicate packages, and invalid versions.
3. Merge only after passing PR checks. The `main` push runs tests but does not publish unless the commit explicitly includes `[publish-selura-store]`; publishing can also be started manually on `main`.
4. Open [Publish Selura Extension Store](https://github.com/zexaldragneel/selura-extensions/actions/workflows/publish-store.yml), click **Run workflow** on `main` if a merge did not publish.
5. The job downloads all 26 prebuilt source APKs, verifies every package and signing certificate SHA-256, extracts icons, generates a 26-item index and replaces generated contents of the `repo` branch **only** after all checks succeed.
6. Verify the public `repo.json`, `index.json`, 26 APKs and 26 icons are reachable under the new owner. Then refresh **Extension stores** and **Extensions** in Selura Manga and test installation/search/chapter pages on Android.

The release index uses signer SHA-256
`da9cfd25f9b1c694b585d427e5faa8c9a1d052b8d846051fbe1569d65c851d42`. Do not publish a different signing identity, since Android would reject updates and Mihon checks store trust against the certificate.

## Data compatibility

- Existing NHentai/MangaDex and six previously published extensions remain unchanged; keep the original source ID derivation for each language.
- 18 new extensions use distinct Android APK package identities, `source.versionId = 7301`, and deterministic SHA-256 based remapping of pinned explicit legacy IDs. Preserve all these for future updates.
- The store only changes downloadable metadata, not the device library, categories, bookmarks, reading progress or downloaded chapters. Do not silently migrate or replace entries.
- Source builds are Apache-2.0 derivatives pinned to Keiyoushi at `ff521c17bb3e503c01e658e8fac00b60a95829f3`, not yet wholly independent from its shared Gradle/build code.
- Do not claim actual online source functionality without device tests. Never bypass site authentication or restrictions.
