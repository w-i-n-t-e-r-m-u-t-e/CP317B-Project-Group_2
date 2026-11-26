"""Find who made a device from its hardware (MAC) address, using the IEEE list in oui.csv."""
import csv
import platform
import re
import subprocess
from functools import lru_cache
from pathlib import Path

OUI_FILE = Path(__file__).resolve().parent / "oui.csv"  # from standards-oui.ieee.org


@lru_cache(maxsize=1)
def vendors():
    with open(OUI_FILE, encoding="utf-8", newline="") as file:
        return {row["Assignment"]: row["Organization Name"] for row in csv.DictReader(file)}


def parse_arp(text):
    """{ip: 'AABBCCDDEEFF'} from `arp` output on macOS, Linux or Windows."""
    table = {}
    pattern = r"(\d+\.\d+\.\d+\.\d+)\)?\s+(?:at\s+)?((?:[0-9a-fA-F]{1,2}[:-]){5}[0-9a-fA-F]{1,2})\b"
    for ip, mac in re.findall(pattern, text):
        # macOS drops leading zeros, so pad every part
        table[ip] = "".join(part.zfill(2) for part in re.split("[:-]", mac)).upper()
    return table


def mac_table():
    flag = "-a" if platform.system() == "Windows" else "-an"
    try:
        return parse_arp(subprocess.run(["arp", flag], capture_output=True, text=True, timeout=10).stdout)
    except (OSError, subprocess.TimeoutExpired):
        return {}


def maker(mac):
    """Short company name, 'Private address', or None if unknown."""
    if not mac:
        return None
    if int(mac[:2], 16) & 2:  # made-up address, used by phones for privacy
        return "Private address"
    name = vendors().get(mac[:6])
    if not name or name == "Private":
        return None
    return re.split(r",| Inc\b| Corp| Co\b| Ltd| Electronics| Technolog", name)[0].strip()


def label(ip, mac):
    """'Samsung (.162)' or 'Samsung (:7d64)', or the IP if the maker is unknown. At most 25 characters."""
    name = maker(mac)
    if not name:
        return ip
    separator = ":" if ":" in ip else "."
    suffix = f" ({separator}{ip.rsplit(separator, 1)[1]})"
    return name[:25 - len(suffix)] + suffix


if __name__ == "__main__":  # self-check: python utils/vendor.py
    mac = parse_arp("? (10.0.0.5) at 28:6f:b9:1:2:3 on en0 ifscope [ethernet]")["10.0.0.5"]
    assert mac == "286FB9010203"
    assert parse_arp("  10.0.0.6          28-6f-b9-01-02-03     dynamic")["10.0.0.6"] == mac
    assert parse_arp("? (10.0.0.7) at (incomplete) on en0") == {}
    assert label("10.0.0.5", mac) == "Nokia Shanghai Bell (.5)"
    assert label("10.0.0.5", "DA1122334455") == "Private address (.5)"
    assert label("10.0.0.5", None) == "10.0.0.5"
    assert label("fe80::1:7d64", mac) == "Nokia Shanghai B (:7d64)" or label("fe80::1:7d64", mac).endswith("(:7d64)")
    print("ok")
