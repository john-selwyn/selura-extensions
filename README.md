# Selura Extensions

An independently managed **extension store** for the [Selura Manga Android reader](https://github.com/john-selwyn/selura-reader).

This repository distributes Selura-maintained Android manga source extensions. It is not affiliated with the official Mihon, Keiyoushi or Yūzōnō projects.

## Available extensions

- **Selura NHentai v2** — a separately packaged, optimized nHentai.net adapter. Adult content; for authorized adult users only. Based on appropriately attributed Apache-2.0 Yūzōnō source.
- **Selura MangaDex** — a separately packaged, Keiyoushi-derived MangaDex adapter. Based on appropriately attributed Apache-2.0 Keiyoushi source.

The source code and original verified CI builds are maintained in the owner's **private** `selura-reader` repository. This public repository hosts the independently **signed APKs** and a Mihon-compatible JSON index without exposing the signing key or private repository code. Public catalog generated from signed releases by [GitHub Actions run #39410027167](https://github.com/john-selwyn/selura-extensions/actions/runs/39410027167).

## Android setup

**Add Selura Extensions using this verified URL:**

`https://raw.githubusercontent.com/john-selwyn/selura-extensions/repo/repo.json`

The [live catalog](https://raw.githubusercontent.com/john-selwyn/selura-extensions/repo/index.json) currently lists two extensions. Its APKs and icons are published on the [`repo` branch](https://github.com/john-selwyn/selura-extensions/tree/repo). This is a public extension catalog, not an APK or app install URL.

On Android, use Selura Manga → Browse → Extensions → Extension stores → Add and paste the `repo.json` URL shown above. Existing Keiyoushi and Yūzōnō stores remain independent and should not be removed.

## Security and source migration

The extension APKs use the existing Selura signing certificate. This store does **not** relabel third-party APKs as official upstream builds, bypass providers' authentication, silently replace installed extensions, or migrate library entries to new source IDs. Preserve reading history and downloads; perform source migration separately with backup protection.

Development and automated release controls are documented in [STORE_MAINTENANCE.md](STORE_MAINTENANCE.md).
