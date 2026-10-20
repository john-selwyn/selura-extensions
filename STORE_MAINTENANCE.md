# Selura Extension Store — Maintenance

## Architecture

- Public store: `john-selwyn/selura-extensions` (this repository).
- Private development: `john-selwyn/selura-reader`, extension PR #25 and PR #26.
- Signed release artifacts: two **already built and signed** APKs from the private repository.
- Public generated branch: `repo`, containing `repo.json`, `index.json`, `apk/` and `icon/`. The branch is created **only after a successful publication workflow**.
- Store URL for Android (do not add until published):
  `https://raw.githubusercontent.com/john-selwyn/selura-extensions/repo/repo.json`

Mihon-compatible JSON `repo.json` redirects to `index.json`; this uses the same model fields as the Mihon extension store. Published icons are extracted from the signed source APKs. Both packages are independent from official Yuzono and Keiyoushi packages, so **do not uninstall other extensions**.

## One-time account setup — read-only token

GitHub's default `GITHUB_TOKEN` cannot read the owner's separate private repository. A narrowly scoped fine-grained personal access token is required **only to download existing signed release APKs**, not to compile or sign code.

1. Open https://github.com/settings/personal-access-tokens/new and set token name `Selura public extension store read access`.
2. Resource owner: `john-selwyn`. Select **Only select repositories** → `selura-reader`.
3. Repository permissions → **Contents: Read-only** (Metadata: Read automatically).
4. Choose an expiration/renewal plan. Generate the token and copy the token value immediately. **Never paste it in ChatGPT, an issue, PR, public source file or commit**.
5. Visit https://github.com/john-selwyn/selura-extensions/settings/secrets/actions, select **New repository secret**:
   - Name: `SELURA_READER_READ_TOKEN`
   - Secret: paste the new token
6. Once the workflow is merged into `main`, open https://github.com/john-selwyn/selura-extensions/actions/workflows/publish-store.yml and click **Run workflow** on `main`.

The token is read-only for `selura-reader`. Publication uses this public repository's own short-lived Actions `GITHUB_TOKEN` with `contents: write`, scoped to `selura-extensions`. The production signing certificate **never leaves the private repository**; no encrypted keystore or signing password is exposed here.

## Release / verification protocol

The publisher pulls these pinned and previously verified releases:

| Extension | Private release tag | File |
| --- | --- | --- |
| Selura NHentai v2 (Android-tested) | `test-selura-source-pr-25-run-12` | `selura-nhentai.apk` |
| Selura MangaDex (CI-passed, phone test pending) | `test-selura-mangadex-pr-26-run-3` | `selura-mangadex.apk` |

Before publishing, CI verifies Android APK signatures, checks SHA-256 against the expected existing Selura certificate, enforces distinct packages, reads real `versionCode` and `versionName` from Android manifests, and generates exact-language source IDs using upstream's documented MD5 ID algorithm. Any failure prevents store publication. Both APKs must share the expected certificate.

**Important:** Real users must still test the store add/install flow and Selura MangaDex browse/chapters on Android. Successful compilation and store metadata checks do not prove online source functionality.

### Updating extensions

New APKs must first be built and device-checked in the private source repo with the **same signing key** and monotonically increasing Android `versionCode`. Then update the release tags in `.github/workflows/publish-store.yml` through a reviewed PR, run unit tests and repeat the manual publication. The `repo` branch and URL stay stable while APKs and index versions update.

Do not copy Keiyoushi's full extension feed, third-party extensions or untested binaries into this store without an explicit supported-source and licensing decision. Do not overwrite user library source IDs, downloads, or reading history as part of store updates.

## Security notes

- The PAT is read-only for the separate private repository and stored only in GitHub Actions secrets.
- Workflow permission to write is limited to this public repository's generated `repo` branch.
- PR test jobs do **not** receive the private token and cannot publish.
- Never publish the private signing key, encrypted keystore, secret password, private repository source, or credentials.
- Store catalogs and APKs are public once released. Only licensed/open-source components and authorized source integrations are supported.
