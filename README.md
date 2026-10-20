# Selura Extensions

Independent public extension catalog for [Selura Manga](https://github.com/zexaldragneel/selura-reader), built with the native Mihon Android engine. Selura is not affiliated with Mihon, Keiyoushi or Yūzōnō.

## Extension store URL (unchanged Android experience)

```
https://raw.githubusercontent.com/zexaldragneel/selura-extensions/repo/repo.json
```

The store maintains **26 separately signed manga extensions**: 8 pre-existing source packages plus the 18 new orphaned-source derivatives (NHentai is **not** duplicated). Provider names appear naturally, without a "Selura" prefix.

The original 8 are NHentai, MangaDex, MANGA Plus by SHUEISHA, Webtoons.com, MangaFire, MangaPill, MangaKatana and Mangabat.

The new 18 are 3Hentai, AllPornComic, Asura Scans, Doujins, Flame Comics, HDoujin, Hentai4Free, HentaiHand, HentaiRead, Hiperdex, Hive Scans, MangaGeko, Mangakakalot, Mgread.io, ToonGod, Toonily, Vortex Scans and WebtoonXYZ. Some are adult-only; the reader may hide them depending on content filters.

**Build and repository publishing are not evidence that a content provider works at runtime.** Test extensions on Android before relying on them.

## How to use

1. In Selura Manga open **Browse → Extensions → Extension stores**.
2. If Selura Extensions already exists, refresh the store. Otherwise, add the `repo.json` URL above. Keep the previous entry until the new catalog is verified; do not delete your other repositories.
3. Return to **Browse → Extensions** and refresh. The 26 entries should appear with individual download icons when the published catalog is live.
4. Install one or two sources and trust them in Selura. Search for manga, read an entire chapter and verify existing library entries are still available.

The catalog endpoint contains the JSON metadata and public signed APK/icon URLs. The main Selura Android APK and existing reading data are not altered by a store update.

## Release ownership and source identity

- `zexaldragneel/selura-reader` builds and signs APKs in GitHub Actions and publishes immutable prereleases.
- This repository publishes **verified** APKs and a Mihon-compatible `index.json` from those immutable releases. No private signing key is published or imported.
- The original 8 Android packages and source IDs remain unchanged.
- The new 18 use distinct `selura...` internal Android packages and the immutable `versionId=7301` source family. Legacy explicit source IDs are remapped deterministically to avoid taking over already-installed source identities; the new source IDs must not change after publishing.
- Apache-2.0 upstream licensing and required attribution are preserved. Providers' login rules and access controls must be respected.

See [STORE_MAINTENANCE.md](STORE_MAINTENANCE.md) for security, signing verification, and publishing details.
