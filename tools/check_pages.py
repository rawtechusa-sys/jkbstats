#!/usr/bin/env python3
"""
check_pages.py -- load every tab of the site in headless Edge/Chrome against the
LOCAL data/ directory and report JavaScript console errors.

    python tools/check_pages.py                 # all tabs
    python tools/check_pages.py streams tts     # some tabs
    python tools/check_pages.py --dump streams  # also print the rendered text

config.js serves data from the page's own directory when the host is localhost,
so this needs no GitHub repo -- only a populated data/ (see the collector's
backfill_channel.py + rebuild_all.py).

Exit code 1 when any tab logs a console error or an uncaught exception.
"""

import argparse
import functools
import http.server
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
TABS = ["streams", "channelstats", "donors", "tts", "chat"]
BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
]
# chromium logs page console output as one of
#   [pid:tid:date:LEVEL:CONSOLE(line)] "msg", source: url (line)
#   [pid:tid:date:LEVEL:CONSOLE:line] "msg", source: url (line)
# Some builds log EVERY console line (console.error and uncaught exceptions
# included) at level INFO, so the level alone can't classify a line.
CONSOLE_RE = re.compile(r':(INFO|WARNING|ERROR):CONSOLE[(:](\d+)\)?\] "(.*)", source: (\S*)')
ERROR_HINTS = ("Uncaught", "is not defined", "is not a function", "SyntaxError",
               "TypeError", "ReferenceError", "Cannot read", "Failed to")


class _Quiet(http.server.SimpleHTTPRequestHandler):
    missing: list = []

    def log_message(self, *args):
        pass

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            _Quiet.missing.append(self.path)
        super().send_error(code, message, explain)


class _Server(http.server.ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        pass    # the headless browser drops sockets on exit; not worth a traceback


def find_browser() -> str:
    for path in BROWSERS:
        if os.path.exists(path):
            return path
    for name in ("msedge", "chromium", "google-chrome", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit("No Edge/Chrome/Chromium found for the headless check.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tabs", nargs="*", default=TABS)
    ap.add_argument("--dump", action="store_true", help="print each tab's rendered text")
    ap.add_argument("--budget", type=int, default=9000, help="virtual time per tab, ms")
    ap.add_argument("--hash", default=None,
                    help="full location hash to load in place of the tab slug, e.g. streams/<stream_id>")
    args = ap.parse_args()

    handler = functools.partial(_Quiet, directory=str(SITE))
    server = _Server(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    browser = find_browser()

    bad = 0
    for tab in args.tabs:
        _Quiet.missing = []
        target = args.hash if args.hash else tab
        # ignore_cleanup_errors: the browser can still hold profile files for a
        # moment after it exits (Windows).
        with tempfile.TemporaryDirectory(prefix="jkb_check_", ignore_cleanup_errors=True) as profile:
            # A log FILE, not stderr: on Windows the browser is a GUI-subsystem
            # process and --enable-logging=stderr writes nothing we can capture.
            log_path = os.path.join(profile, "console.log")
            proc = subprocess.run(
                [browser, "--headless=new", "--disable-gpu", "--no-first-run",
                 f"--user-data-dir={profile}", "--enable-logging", "--v=0",
                 f"--log-file={log_path}",
                 f"--virtual-time-budget={args.budget}", "--dump-dom",
                 f"http://127.0.0.1:{port}/index.html#{target}"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            try:
                console = Path(log_path).read_text(encoding="utf-8", errors="replace")
            except OSError:
                console = ""
        if not console:
            print(f"FAIL #{target}   the browser wrote no log -- console capture is broken")
            bad += 1
            continue
        errors, notes = [], []
        for line in console.splitlines() + proc.stderr.splitlines():
            m = CONSOLE_RE.search(line)
            if not m:
                continue
            level, lineno, msg, source = m.groups()
            if not source.startswith("http://127.0.0.1"):
                continue                     # browser-internal extension chatter
            if msg.startswith("Tracking Prevention blocked"):
                continue                     # Edge noise about the CDN scripts
            where = f"{source.rsplit('/', 1)[-1]}:{lineno}"
            is_error = level == "ERROR" or any(h in msg for h in ERROR_HINTS)
            (errors if is_error else notes).append(f"{level:7} {where}  {msg[:300]}")
        missing = [p for p in _Quiet.missing if "favicon" not in p]
        status = "FAIL" if errors else "ok  "
        print(f"{status} #{target}   ({len(errors)} error(s), {len(notes)} other console line(s), "
              f"{len(missing)} 404(s))")
        for e in errors:
            print("     " + e)
        for n in notes[:8]:
            print("     " + n)
        for p in missing[:12]:
            print("     404 " + p)
        if args.dump:
            # The console may be cp1252 (Windows); never crash on a page glyph.
            sys.stdout.buffer.write(proc.stdout[:6000].encode("utf-8", "replace") + b"\n")
        bad += bool(errors)
    server.shutdown()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
