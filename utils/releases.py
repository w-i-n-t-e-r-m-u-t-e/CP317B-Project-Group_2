"""Latest versions and end-of-support dates for common systems, from https://endoflife.date.

Only the product name (such as "macos") is sent; nothing about your devices.
"""
import json
from datetime import date
from urllib.request import urlopen
from utils.version import parse

# device type (lower case) -> product name on endoflife.date
PRODUCTS = {"macos": "macos", "ios": "ios", "windows": "windows", "ubuntu": "ubuntu", "android": "android"}
# only these publish a "latest" that can be compared with what a device reports
COMPARABLE = {"macos", "ios"}
cache = {}  # product -> list of releases, or [] if it could not be fetched


def missing(types):
    """Products needed for these device types that have not been fetched yet."""
    return sorted({PRODUCTS[t.lower()] for t in types if t.lower() in PRODUCTS} - set(cache))


def load(products):
    for product in products:
        try:
            with urlopen(f"https://endoflife.date/api/{product}.json", timeout=5) as response:
                cache[product] = json.load(response)
        except (OSError, ValueError):
            cache[product] = []  # shown as Unknown; tried again next time the app starts


def release_for(kind, version):
    """The release line a version belongs to (26.6 -> the "26" line), or None."""
    product = PRODUCTS.get((kind or "").lower())
    numbers = parse(version)
    if not product or not numbers:
        return None
    releases = cache.get(product, [])
    if product == "windows":  # matched by build number; "-w" lines are the home editions
        found = [r for r in releases if parse(r.get("latest")) == numbers]
        return next((r for r in found if r["cycle"].endswith("-w")), found[0] if found else None)
    for release in releases:
        line = parse(release["cycle"].split("-")[0])
        if line and numbers[:len(line)] == line:
            return release
    return None


def status(kind, version, today=None):
    """UPDATED, OUTDATED, UNSUPPORTED (no more security updates), SUPPORTED (patch level unknown) or UNKNOWN."""
    release = release_for(kind, version)
    if not release:
        return "UNKNOWN"
    end = release.get("eol")
    if end is True or (isinstance(end, str) and end <= (today or date.today().isoformat())):
        return "UNSUPPORTED"
    if kind.lower() in COMPARABLE and release.get("latest"):
        return "OUTDATED" if parse(version) < parse(release["latest"]) else "UPDATED"
    return "SUPPORTED"


if __name__ == "__main__":  # self-check: python -m utils.releases
    cache["macos"] = [{"cycle": "26", "latest": "26.7.3", "eol": False},
                      {"cycle": "13", "latest": "13.7.8", "eol": "2025-09-15"}]
    cache["windows"] = [{"cycle": "11-25h2-w", "latest": "10.0.26200", "eol": "2027-10-12"}]
    assert status("macOS", "26.6", "2026-11-26") == "OUTDATED"
    assert status("macOS", "26.7.3", "2026-11-26") == "UPDATED"
    assert status("macOS", "13.7.8", "2026-11-26") == "UNSUPPORTED"
    assert status("Windows", "10.0.26200", "2026-11-26") == "SUPPORTED"
    assert status("Windows", "10.0.1", "2026-11-26") == "UNKNOWN"
    assert status("Toaster", "1", "2026-11-26") == "UNKNOWN"
    print("ok")
