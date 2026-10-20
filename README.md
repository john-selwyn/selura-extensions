# Selura Extensions

An independently managed **extension store** for the [Selura Manga Android reader](https://github.com/john-selwyn/selura-reader).

This repository distributes Selura-maintained Android manga source extensions. It is not affiliated with the official Mihon, Keiyoushi or Yūzōnō projects.

## Current extensions (pending store publication)

- **Selura NHentai v2** — a separately packaged, optimized nHentai.net adapter. Adult content; for authorized adult users only. Based on appropriately attributed Apache-2.0 Yūzōnō source.
- **Selura MangaDex** — a separately packaged, Keiyoushi-derived MangaDex adapter. Based on appropriately attributed Apache-2.0 Keiyoushi source.

The original sources, signed APKs and recorded CI builds are currently in the owner's **private** `selura-reader` repository. The public store will publish the **already-signed** APKs and a Mihon-compatible JSON index without disclosing the signing key or private repository code.

## Android setup

The store URL will be published once the GitHub Actions **Publish Selura Extension Store** workflow completes successfully. Do **not** add a placeholder URL until its index and APKs are publicly accessible.

After publication, use Selura Manga → Browse → Extensions → Extension stores → Add and paste the published `repo.json` URL. Existing Keiyoushi and Yūzōnō stores remain independent and should not be removed.

## Security and source migration

The extension APKs use the existing Selura signing certificate. This store does **not** relabel third-party APKs as official upstream builds, bypass providers' authentication, silently replace installed extensions, or migrate library entries to new source IDs. Preserve reading history and downloads; perform source migration separately with backup protection.

Development and automated release controls are documented in [STORE_MAINTENANCE.md](STORE_MAINTENANCE.md).
