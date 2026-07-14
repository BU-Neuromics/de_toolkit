# Vendored charting libraries

These minified bundles are vendored (committed, not built) so `detk-report` can
produce a single self-contained, offline HTML file with no CDN dependency and no
JavaScript build step. All three are permissively licensed (BSD-3-Clause),
compatible with de_toolkit's MIT license.

| File | Library | Version | License |
|------|---------|---------|---------|
| `vega.min.js` | [Vega](https://vega.github.io/vega/) | 5.33.1 | BSD-3-Clause |
| `vega-lite.min.js` | [Vega-Lite](https://vega.github.io/vega-lite/) | 5.x | BSD-3-Clause |
| `vega-embed.min.js` | [vega-embed](https://github.com/vega/vega-embed) | 6.x | BSD-3-Clause |

Fetched from jsDelivr on 2026-07-14. To refresh (pin exact versions when doing so):

```
curl -fsSL https://cdn.jsdelivr.net/npm/vega@5       -o vega.min.js
curl -fsSL https://cdn.jsdelivr.net/npm/vega-lite@5  -o vega-lite.min.js
curl -fsSL https://cdn.jsdelivr.net/npm/vega-embed@6 -o vega-embed.min.js
```
