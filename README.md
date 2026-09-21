# Goblin Watch

Live-stream statistics site for the YouTube channel
[`@Jayhooft`](https://www.youtube.com/@Jayhooft) (JKB). It is the goblin-sized
counterpart of Ogre Watch.

The site is static: plain HTML, CSS, and JavaScript with Chart.js from a CDN.
There is no build step. The `collector/` project (a separate repo) writes all of `data/`.

## Pages

| Tab | File | Shows |
|---|---|---|
| Streams | `streams.html` | One stream: viewers, chat rate, active chatters, donations, and the VOD. A live stream refreshes each 300 s. |
| Channel Stats | `channelstats.html` | All streams over time: subscribers, peak and average viewers, donations, chat rate. |
| Donors | `donors.html` | The Goblin Hoard: Super Chat and membership totals per user. |
| TTS | `tts.html` | tts.monster usage: sound effects `(bonk)` and voices `pooh:`. |
| Search | `chat.html` | Search of all chat logs and transcripts, with links into the VOD. |

`index.html` is the shell. It holds the tabs, the theme selector, and the time zone selector.

## Where the data comes from

Each page reads JSON from `DATA_BASE` (see `config.js`):

- In production: `raw.githubusercontent.com/<owner>/<repo>/main`. A data commit is
  visible at once. It needs no Pages deploy, so `deploy.yml` ignores `data/**`.
- On `localhost`: the files beside the page. This permits a preview without a repo.

Past streams (rebuilt from the chat replay) have no viewer counts. YouTube does
not keep that data.

## Before the first deploy

1. Done: the repo is `rawtechusa-sys/jkbstats` (`GITHUB_REPO` in `config.js`).
2. Done: `SITE_URL` and `CNAME` are set to `rtudaycare.center`.
3. Confirm the streamer time zone in `TZ_MODES.streamer` (`config.js`).
4. In the repo settings, set Pages to "GitHub Actions". Point the domain's DNS at GitHub Pages.
5. Give the collector a fine-grained token for this repo (Contents: read and write).

## Local preview and page check

```
python -m http.server 8000          # then open http://localhost:8000/
python tools/check_pages.py         # headless Edge/Chrome: reports JavaScript errors per tab
```

`check_pages.py` needs a populated `data/`. The collector's `backfill_channel.py`
and `rebuild_all.py` make one.

## TTS lists

`tts-voices.txt` and `tts-sounds.txt` hold the channel's tts.monster catalog, one
name per line. The collector's `refresh_tts_catalog.py --site <this dir>` writes them.
`tts-descriptions.md` and `tts-backgrounds/` are optional and start empty.

## Themes

`themes/goblin-cave.css` (default), `hearth-fire.css`, `misty-mountain.css`,
`deep-mine.css`, `the-shire.css`. Each file sets the same CSS variables.
