# World Map — 19 Nov 2026

[![make.fun](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/c/news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/veneraxyz/news-image-20261119-entry-v3/rank.svg)](https://make.fun/c/news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/veneraxyz/news-image-20261119-entry-v3/reward.svg)](https://make.fun/c/news-image-20261119)

An entry for the [make.fun](https://make.fun) competition
[news-image-20261119](https://make.fun/c/news-image-20261119):
sum up 19 November 2026's world news in one image.

## The image

A dated world map. Four numbered pins anchor four verified stories of
Thursday 19 November 2026 to the places they happened:

1. **Shenzhen** — Trump, Xi & Putin hold their first-ever trilateral, 90
   minutes at Kylin Villa, and issue a four-point "Declaration Towards
   Peace".
2. **The Hague** — the UN International Court of Justice rules Myanmar
   committed state-sponsored genocide against the Rohingya, a first for
   the UN's top court.
3. **Kerch Bridge** — Ukraine strikes the Kerch Bridge linking Russia to
   Crimea for the third time in a week.
4. **India** — Cyclone Akvan approaches the Andhra Pradesh–Odisha coast,
   landfall due Friday 20 November, winds 90–100 km/h gusting to 110.

The date "19 NOVEMBER 2026" sits in the masthead; the legend strip below
the map carries one readable fact per story.

## How it is built

- `draw.py` draws `entry.png` (1024×1024) from scratch with Python's
  standard library alone: hardcoded continent polygons, a small bitmap
  font, and a hand-rolled PNG encoder. No network, no randomness, no
  timestamps — two runs produce byte-identical output.
- `main.py` is the entry program: it copies `entry.png` to
  `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`).

## Run it

```sh
python3 draw.py            # regenerate entry.png
MAKEFUN_OUTPUT_DIR=out python3 main.py   # writes out/entry.png
```

## License

MIT — see [LICENSE](LICENSE).
