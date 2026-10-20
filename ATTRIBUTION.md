# Upstream Attributions and Derivative Notices

The Selura extension store publishes **independently packaged, modified source extensions**. These are not official extensions from Mihon, Keiyoushi, Cursed Yūzōnō, MangaDex or the underlying content websites.

## Selura NHentai

- Original code: [Yuzono/Cursed Manga Extensions](https://github.com/yuzono/cursed-manga-extensions), `src/all/nhentai`, pinned source revision `5dad5cf65dce98bb05ba8edf1f38770585e032b9`.
- Original version reference: NHentai 1.4.62 (the Cursed Yūzōnō adapter).
- License: Apache License, Version 2.0 (see [LICENSE](LICENSE)).
- Selura modifications: separate package `eu.kanade.tachiyomi.extension.all.seluranhentai`, separate source IDs, stabilized image CDN selection, limited image fallback and network timeouts, error handling and source naming. Original extension unchanged.
- Adult-oriented source; source availability depends on the website's terms and connectivity. Authentication restrictions and rate limits are respected.

## Selura MangaDex

- Original code: [Keiyoushi Extension Sources](https://github.com/keiyoushi/extensions-source), `src/all/mangadex`, pinned source revision `ff521c17bb3e503c01e658e8fac00b60a95829f3`.
- License: Apache License, Version 2.0 (see [LICENSE](LICENSE)).
- Selura modifications: separate package `eu.kanade.tachiyomi.extension.all.seluramangadex`, separate generated source IDs, Selura network identification, source name and versioning, and disabled conflicting deep-link capture. Original extension unchanged.

## Planned first expansion — six Keiyoushi-derived providers

The following are **separate Selura-maintained Android extension packages** adapted from the Apache-2.0 licensed Keiyoushi extension source repository pinned to commit `ff521c17bb3e503c01e658e8fac00b60a95829f3`:

| Name shown in Selura | Upstream source module | Separate package suffix |
| --- | --- | --- |
| MANGA Plus by SHUEISHA | `src/all/mangaplus` | `all.seluramangaplus` |
| Webtoons.com | `src/all/webtoons` | `all.selurawebtoons` |
| MangaFire | `src/all/mangafire` | `all.seluramangafire` |
| MangaPill | `src/en/mangapill` | `en.seluramangapill` |
| MangaKatana | `src/en/mangakatana` | `en.seluramangakatana` |
| Mangabat | `src/en/mangabat` | `en.seluramangabat` |

Modifications: independent Android application package suffixes, source ID `versionId=2` for non-colliding source identities while preserving the original site display names, removed duplicate deep-link intent interception, independent Selura signing, and retained upstream LICENSE/provenance. Existing original Keiyoushi and Selura packages remain untouched. Content listings and website availability depend on each upstream service and its conditions.

**Release status:** The additional APKs must pass independent Gradle build, Android signature, package and index validation before inclusion in the public store. Site functionality still requires Android testing; successful compilation does not guarantee live provider compatibility.

All original relevant copyright and attribution notices must remain in the corresponding source checkout or derivative source module. Publishing an extension APK does not confer rights to any manga content.

The releases are signed with Selura's existing certificate. The public store does **not** hold any signing private key or the credentials used to access the owner's private development repository.
