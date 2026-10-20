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

All original relevant copyright and attribution notices must remain in the corresponding source checkout or derivative source module. Publishing an extension APK does not confer rights to any manga content.

The releases are signed with Selura's existing certificate. The public store does **not** hold any signing private key or the credentials used to access the owner's private development repository.
