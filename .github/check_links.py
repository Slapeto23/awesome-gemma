"""Minimalni kontrola odkazu v markdown souborech (stdlib only)."""
import re
import sys
import urllib.request

# Zname odkazy, ktere bot neumí overit (vyzaduji login / zmenena deep-link
# struktura na cizim webu). Nutno zkontrolovat rucne v prohlizeci.
ALLOWLIST = {
    # Google Cloud Console vyzaduje prihlaseni (bot redirect-loop).
    "https://console.cloud.google.com/agent-platform/publishers/google/model-garden/gemma4",
    # 404 k 15.10.2026, koren webu zije - deep link se presunul.
    "https://inference-docs.cerebras.ai/models/gemma-4-31b",
    # 404 k 15.10.2026, koren docs zije - deep link se presunul.
    "https://modal.com/docs/launch/gemma-4",
}

URL_RE = re.compile(r"https?://[^\s)\"'<>`]+")
# Koncova interpunkce neni soucasti URL.
TRAILING = ".,;:!?)'\""


def urls_in(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    found = []
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(TRAILING)
        if url not in found:
            found.append(url)
    return found


def check(url):
    """Vrat (ok, info). HEAD, pri neuspechu GET; jeden retry."""
    for attempt in (1, 2):
        for method in ("HEAD", "GET"):
            try:
                req = urllib.request.Request(
                    url,
                    method=method,
                    headers={"User-Agent": "linkcheck (repo CI)"},
                )
                with urllib.request.urlopen(req, timeout=20) as r:
                    if r.status < 400:
                        return True, str(r.status)
            except Exception as e:  # noqa: BLE001 - libovolna sitova chyba = KO
                last = e
        if attempt == 2:
            return False, str(last)
    return False, str(last)


def main(paths):
    failed = []
    total = 0
    for path in paths:
        for url in urls_in(path):
            if url in ALLOWLIST:
                continue
            total += 1
            ok, info = check(url)
            print(("OK   " if ok else "FAIL ") + url + " (" + info + ")")
            if not ok:
                failed.append(url)
    print(str(total) + " odkazu, rozbitych: " + str(len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["README.md"]))
