# Selura Extensions

An independently managed **extension store** for the [Selura Manga Android reader](https://github.com/john-selwyn/selura-reader).

This repository distributes Selura-maintained Android manga source extensions. It is not affiliated with the official Mihon, Keiyoushi or Yūzōnō projects.

## Available extensions — 8 signed APKs

| Extension name shown in the catalog | Original provider / type |
| --- | --- |
| NHentai | nHentai.net, adults only; optimized Yūzōnō-derived adapter |
| MangaDex | MangaDex, Keiyoushi-derived adapter |
| MANGA Plus by SHUEISHA | Official Shueisha manga service |
| Webtoons.com | Webtoons and webcomics |
| MangaFire | Manga source |
| MangaPill | Manga source |
| MangaKatana | Manga source |
| Mangabat | Manga source |

The store **does not prepend “Selura” to catalog titles**. Existing MangaDex and NHentai APK package identities and source IDs remain unchanged to preserve library compatibility. Their currently installed extension labels may still reflect older APK branding; updating them safely is a separate milestone.

The public catalog is updated by [the successful eight-extension publication run](https://github.com/john-selwyn/selura-extensions/actions/runs/39415154196). Signed APK builds and source files remain in the separate **private** `selura-reader` repository; the public store contains only verified signed APKs, icons and its index. No signing private keys are published.

## Android setup

**Add Selura Extensions using this verified URL:**

`https://raw.githubusercontent.com/john-selwyn/selura-extensions/repo/repo.json`

The [live catalog](https://raw.githubusercontent.com/john-selwyn/selura-extensions/repo/index.json) currently lists eight extensions. Its APKs and icons are published on the [`repo` branch](https://github.com/john-selwyn/selura-extensions/tree/repo). This is a public extension catalog, not an APK or app install URL.

On Android, use Selura Manga → Browse → Extensions → Extension stores → Refresh (if already added), then return to the Extensions list and refresh it. For a first-time setup, tap Add and paste the `repo.json` URL above. Existing Keiyoushi and Yūzōnō stores remain independent and should not be removed.

## Security and source migration

The extension APKs use the existing Selura signing certificate. This store does **not** relabel third-party APKs as official upstream builds, bypass providers' authentication, silently replace installed extensions, or migrate library entries to new source IDs. Preserve reading history and downloads; perform source migration separately with backup protection.

Development and automated release controls are documented in [STORE_MAINTENANCE.md](STORE_MAINTENANCE.md).
