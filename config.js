// ── Goblin Watch Frontend Config ───────────────────────────────────────────────
// Edit this file to configure the dashboard without touching the pages.

// ── Site ───────────────────────────────────────────────────────────────────────
const SITE_TITLE     = 'Goblin Watch';
const SITE_URL       = 'https://rtudaycare.center';
const CHANNEL_NAME   = 'JKB';
const CHANNEL_HANDLE = '@Jayhooft';
const CHANNEL_URL    = 'https://www.youtube.com/@Jayhooft';

// ── GitHub repo (site + data) ──────────────────────────────────────────────────
const GITHUB_OWNER = 'rawtechusa-sys';
const GITHUB_REPO  = 'jkbstats';
const BRANCH       = 'main';

// Where the pages fetch data/ (and the tts-*.txt lists) from.
// Production: raw.githubusercontent.com -- a data commit is visible as soon as it
// lands, with no Pages deploy (deploy.yml ignores data/ for exactly that reason).
// Local preview (python -m http.server in this dir): the files next to the page,
// so the site can be checked before the repo exists.
const IS_LOCAL_PREVIEW = ['localhost', '127.0.0.1', ''].includes(location.hostname);
const DATA_BASE = IS_LOCAL_PREVIEW
  ? '.'
  : `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${BRANCH}`;

// While a stream is live (metadata.end_ts == null) the Streams page re-fetches
// it this often. Matches the collector's STATS_LIVE_UPLOAD_INTERVAL and the
// ~5 minute raw.githubusercontent.com cache. 0 disables.
const LIVE_REFRESH_SECONDS = 300;

// ── Money ────────────────────────────────────────────────────────────────────────
// Two decimals WITH thousands separators: 150994.24 -> "150,994.24". Shared by
// every page, so a dollar figure reads the same on each tab. No "$": callers add it.
function fmtMoney(n) {
  return Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ── Timezone ─────────────────────────────────────────────────────────────────────
// Shared by every page. The header dropdown (index.html) writes localStorage
// 'goblin-tz'; date helpers call getTimeZone()/withTZ() at render time, so any
// re-render reflects the current mode. 'local' omits timeZone so toLocale* uses the
// visitor's browser zone. Default is Goblin Time (the streamer's clock).
const TZ_MODES = {
  streamer: { label: 'Goblin Time', zone: 'America/New_York' },
  local:    { label: 'Local Time',  zone: undefined },
  utc:      { label: 'UTC',         zone: 'UTC' },
};
function getTZMode() {
  try { const m = localStorage.getItem('goblin-tz'); if (TZ_MODES[m]) return m; } catch (e) {}
  return 'streamer';
}
function getTimeZone() { return TZ_MODES[getTZMode()].zone; }
// Merge the active zone into a toLocale* options object ('local' -> no timeZone key).
function withTZ(opts) {
  const z = getTimeZone();
  return z ? Object.assign({}, opts, { timeZone: z }) : opts;
}
