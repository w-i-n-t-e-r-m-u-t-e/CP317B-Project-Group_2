"""
iot_monitor.py - home network device scanner + firmware update tracker + priority scorer
(Python standard library only - nothing to pip install)

Pipeline:
  1. SCAN      ping sweep -> ARP cache -> IP + MAC for every device
  2. IDENTIFY  vendor lookup (macvendors.com, cached), hostname, role guess
  2b. UPNP     SSDP discovery -> device description XML -> model / firmware (when exposed)
  3. PROBE     quick TCP check of common ports + HTTP "Server" header
  4. TRACK     compare to history (SQLite): new device, firmware updated, etc.
  5. PRIORITIZE match known CVEs, score urgency (CVSS + CISA KEV + EPSS + exposure)

Usage:
  python iot_monitor.py                 full scan of your network
  python iot_monitor.py --offline       no web calls (vendor API, CISA, EPSS)
  python iot_monitor.py --skip-ports    skip the port/HTTP probe
  python iot_monitor.py --skip-upnp     skip UPnP/SSDP discovery
  python iot_monitor.py --demo          run on built-in sample data, no network needed

Files it creates in ./iot_data/ :
  device_overrides.json   YOU fill in model / firmware per MAC (until you add UPnP discovery)
  device_db.json          YOU curate: latest versions, roles, EOL flags, known CVEs per model
  device_history.db       change history (SQLite)
  vendor_cache.json       cached vendor lookups
  last_scan.json          raw results of the last scan

Only scan networks you own or have permission to scan.
"""

import argparse
import hashlib
import ipaddress
import json
import os
import platform
import re
import socket
import sqlite3
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

# ------------------------------------------------------------------ settings
DATA_DIR = "iot_data"
VENDOR_CACHE = os.path.join(DATA_DIR, "vendor_cache.json")
SCAN_FILE = os.path.join(DATA_DIR, "last_scan.json")
HISTORY_DB = os.path.join(DATA_DIR, "device_history.db")
DEMO_DB = os.path.join(DATA_DIR, "demo_history.db")
DEVICE_DB_FILE = os.path.join(DATA_DIR, "device_db.json")
OVERRIDES_FILE = os.path.join(DATA_DIR, "device_overrides.json")

IS_WINDOWS = platform.system() == "Windows"
COMMON_PORTS = [21, 22, 23, 80, 443, 554, 5900, 8000, 8080, 8443, 9100]
HTTP_PORTS = (80, 8080, 8000)

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_URL = "https://api.first.org/data/v1/epss?cve="

HIGH_IMPACT_ROLES = {"router", "gateway", "camera", "doorbell", "nas", "lock", "alarm"}
RISKY_PORTS = {23: "Telnet", 21: "FTP", 554: "unencrypted RTSP video", 5900: "VNC"}
ROLE_HINTS = {
    "camera": ["camera", "cam", "wyze", "hikvision", "dahua", "reolink", "eufy", "arlo"],
    "router": ["router", "gateway", "routerboard", "linksys", "netgear", "ubiquiti", "arris"],
    "nas": ["nas", "synology", "qnap"],
}


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            print(f"(warning: couldn't read {path}: {e})")
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# =========================================================== 1. SCAN (ARP)
def get_local_ip():
    """Find our LAN IP without sending traffic (UDP connect sends nothing)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    finally:
        s.close()


def ping(ip):
    """One quick ping; even a failed one triggers an ARP request."""
    if IS_WINDOWS:
        cmd = ["ping", "-n", "1", "-w", "500", str(ip)]
    else:
        cmd = ["ping", "-c", "1", "-W", "1", str(ip)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def normalize_mac(raw):
    return ":".join(p.zfill(2) for p in re.split(r"[:-]", raw)).lower()


def read_arp_cache():
    """Parse `arp -a` (Windows/macOS/Linux). Returns {ip: mac}."""
    out = subprocess.run(["arp", "-a"], capture_output=True, text=True).stdout
    found = {}
    for line in out.splitlines():
        ip = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", line)
        mac = re.search(r"([0-9a-fA-F]{1,2}(?:[:-][0-9a-fA-F]{1,2}){5})", line)
        if ip and mac:
            found[ip.group(1)] = normalize_mac(mac.group(1))
    return found


def is_real_device(mac):
    if mac in ("ff:ff:ff:ff:ff:ff", "00:00:00:00:00:00"):
        return False
    return not (mac.startswith("01:00:5e") or mac.startswith("33:33"))


def is_randomized_mac(mac):
    """Phones/laptops use 'private' MACs: bit 2 of the first byte is set."""
    return bool(int(mac.split(":")[0], 16) & 0b10)


def scan_network():
    local_ip = get_local_ip()
    net = ipaddress.ip_network(f"{local_ip}/24", strict=False)  # assumes /24
    print(f"Your IP: {local_ip}  |  Scanning {net} (about 10-20 seconds)...")
    with ThreadPoolExecutor(max_workers=64) as pool:
        list(pool.map(ping, net.hosts()))

    devices = []
    for ip, mac in read_arp_cache().items():
        addr = ipaddress.ip_address(ip)
        if addr not in net or addr == net.broadcast_address or not is_real_device(mac):
            continue
        devices.append({
            "ip": ip, "mac": mac,
            "randomized_mac": is_randomized_mac(mac),
            "is_this_machine": ip == local_ip,
            "discovery_method": "arp",
        })
    devices.sort(key=lambda d: ipaddress.ip_address(d["ip"]))
    return devices


# ======================================================== 2. IDENTIFY
def lookup_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


def lookup_vendor(mac, cache, offline):
    """Vendor from the MAC prefix (first 3 bytes) via macvendors.com; ~1 req/sec limit."""
    oui = mac[:8]
    if oui in cache:
        return cache[oui]
    if offline:
        return "Unknown (offline)"
    vendor = None
    try:
        with urllib.request.urlopen(f"https://api.macvendors.com/{oui}", timeout=5) as r:
            vendor = r.read().decode().strip()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            vendor = "Unknown"
        elif e.code == 429:
            time.sleep(2)
            return "Lookup limited (re-run)"
    except Exception:
        return "Lookup failed"
    cache[oui] = vendor or "Unknown"
    time.sleep(1.1)
    return cache[oui]


def add_identity(devices, offline):
    cache = load_json(VENDOR_CACHE, {})
    for d in devices:
        if d["randomized_mac"]:
            d["vendor"] = "Private/randomized MAC"
        else:
            d["vendor"] = lookup_vendor(d["mac"], cache, offline)
        d["hostname"] = lookup_hostname(d["ip"])
        save_json(VENDOR_CACHE, cache)
    return devices


def apply_overrides(devices):
    """Merge in what YOU know (model, firmware_version, role, upnp_exposed, default_creds...)."""
    overrides = load_json(OVERRIDES_FILE, {})
    for d in devices:
        d.update(overrides.get(d["mac"], {}))


def guess_roles(devices):
    """Very rough guess from hostname/vendor. Overrides always win."""
    for d in devices:
        if d.get("role"):
            continue
        text = f"{d.get('hostname', '')} {d.get('vendor', '')}".lower()
        for role, words in ROLE_HINTS.items():
            if any(w in text for w in words):
                d["role"] = role
                break


# ================================================== 2b. UPNP / SSDP DISCOVERY
SSDP_ADDR = ("239.255.255.250", 1900)
MAX_XML_BYTES = 256 * 1024
# UPnP has NO standard firmware field. Some vendors add one under a custom tag.
FIRMWARE_TAGS = ("firmwareversion", "firmware", "fwversion", "softwareversion", "swversion")
WANTED_FIELDS = ("manufacturer", "modelName", "modelNumber", "modelDescription",
                 "friendlyName", "deviceType")  # serialNumber deliberately NOT collected


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # a device must not bounce us to another host


# ProxyHandler({}) = never route LAN requests through a system/corporate proxy
_lan_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)


def parse_ssdp_response(data):
    """Raw SSDP reply -> dict of upper-cased headers."""
    headers = {}
    for line in data.decode("latin-1", errors="replace").split("\r\n")[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().upper()] = value.strip()
    return headers


def ssdp_discover(local_ip, timeout=4.0, target=SSDP_ADDR):
    """Multicast an SSDP M-SEARCH and collect replies. Returns {ip: [header dicts]}."""
    msg = ("M-SEARCH * HTTP/1.1\r\n"
           "HOST: 239.255.255.250:1900\r\n"
           'MAN: "ssdp:discover"\r\n'
           "MX: 2\r\n"
           "ST: ssdp:all\r\n\r\n").encode()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        try:  # pin to the LAN adapter (matters with VPNs / virtual adapters)
            sock.bind((local_ip, 0))
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_ip))
        except OSError:
            pass
        sock.settimeout(0.5)
        for _ in range(2):  # UDP is lossy, so ask twice
            sock.sendto(msg, target)
        replies = {}
        end = time.time() + timeout
        while time.time() < end:
            try:
                data, (ip, _port) = sock.recvfrom(65535)
            except socket.timeout:
                continue
            except ConnectionResetError:  # Windows quirk after sending UDP
                continue
            except OSError:
                break
            replies.setdefault(ip, []).append(parse_ssdp_response(data))
        return replies
    finally:
        sock.close()


def fetch_description(location, source_ip):
    """Download the device description XML - but only from the device that answered."""
    u = urllib.parse.urlparse(location)
    if u.scheme != "http" or u.hostname != source_ip:
        return None  # LOCATION pointing elsewhere is ignored (it could be a trick)
    try:
        with _lan_opener.open(location, timeout=3) as r:
            return r.read(MAX_XML_BYTES)
    except Exception:
        return None


def parse_description(xml_bytes):
    """Pull model / firmware fields out of a UPnP device description."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return {}

    def tag(el):
        return el.tag.split("}")[-1]  # strip the XML namespace

    info = {}
    device = next((e for e in root.iter() if tag(e) == "device"), None)
    if device is not None:
        for child in device:
            if tag(child) in WANTED_FIELDS and child.text and child.text.strip():
                info[tag(child)] = child.text.strip()
    for el in root.iter():
        if tag(el).lower() in FIRMWARE_TAGS and el.text and el.text.strip():
            info["firmware"] = el.text.strip()
            break
    info["xml_hash"] = hashlib.sha1(xml_bytes).hexdigest()[:16]
    return info


def enrich_with_upnp(devices, local_ip, target=SSDP_ADDR):
    """Fill in model / firmware / manufacturer from UPnP where devices expose it."""
    print("Listening for UPnP/SSDP announcements (about 5 seconds)...")
    replies = ssdp_discover(local_ip, target=target)
    by_ip = {d["ip"]: d for d in devices if not d.get("is_this_machine")}
    answered = with_model = with_fw = 0

    for ip, hdrs in replies.items():
        d = by_ip.get(ip)
        if d is None:
            continue
        answered += 1
        d["discovery_method"] = "arp+ssdp"
        d["upnp_server"] = next((h["SERVER"] for h in hdrs if "SERVER" in h), "")

        locations = list(dict.fromkeys(h["LOCATION"] for h in hdrs if "LOCATION" in h))[:3]
        info = {}
        for loc in locations:
            xml = fetch_description(loc, ip)
            info = parse_description(xml) if xml else {}
            if info:
                break
        if not info:
            continue

        d["upnp_manufacturer"] = info.get("manufacturer", "")
        d["upnp_device_type"] = info.get("deviceType", "")
        d["upnp_friendly_name"] = info.get("friendlyName", "")
        d["upnp_model_number"] = info.get("modelNumber", "")
        d["upnp_xml_hash"] = info.get("xml_hash", "")
        if info.get("modelName"):
            d.setdefault("model", info["modelName"])
            with_model += 1
        if info.get("firmware"):
            d["firmware_version"] = info["firmware"]
            with_fw += 1

    print(f"UPnP: {answered}/{len(by_ip)} devices answered, "
          f"{with_model} gave a model name, {with_fw} exposed a firmware version.")


# ========================================================== 3. PROBE
def check_port(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=0.5):
            return port
    except OSError:
        return None


def grab_http_server(ip, port):
    """Read the HTTP 'Server' header - often reveals device software."""
    try:
        req = urllib.request.Request(f"http://{ip}:{port}/", method="HEAD")
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.headers.get("Server", "")
    except urllib.error.HTTPError as e:
        return e.headers.get("Server", "") if e.headers else ""
    except Exception:
        return ""


def probe_devices(devices):
    targets = [d for d in devices if not d.get("is_this_machine")]
    jobs = [(d, p) for d in targets for p in COMMON_PORTS]
    print(f"Probing {len(targets)} device(s) on {len(COMMON_PORTS)} common ports...")
    with ThreadPoolExecutor(max_workers=128) as pool:
        results = list(pool.map(lambda j: (j[0], check_port(j[0]["ip"], j[1])), jobs))
    for d in targets:
        d["open_ports"] = sorted(p for dev, p in results if dev is d and p)

    web = [(d, next(p for p in HTTP_PORTS if p in d["open_ports"]))
           for d in targets if any(p in d["open_ports"] for p in HTTP_PORTS)]
    with ThreadPoolExecutor(max_workers=16) as pool:
        headers = list(pool.map(lambda x: grab_http_server(x[0]["ip"], x[1]), web))
    for (d, _), server in zip(web, headers):
        d["http_server"] = server


# ================================================== 4. TRACK (history)
def init_db(path):
    db = sqlite3.connect(path)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS devices (
            mac TEXT PRIMARY KEY, first_seen REAL, last_seen REAL);
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT, mac TEXT, ts REAL, ip TEXT,
            vendor TEXT, model TEXT, firmware TEXT, fingerprint TEXT);
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, mac TEXT, ts REAL,
            type TEXT, confidence TEXT, detail TEXT);
    """)
    return db


def parse_version(v):
    """'v1.2.10-beta' -> (1, 2, 10). Crude but fine for most IoT version strings."""
    return tuple(int(n) for n in re.findall(r"\d+", v or ""))


def fingerprint(d):
    """
    Hash of observable traits EXCLUDING firmware version. If this changes while the
    version is unknown, the device may have been updated. Open ports are deliberately
    excluded: they flicker between scans and would cause false alarms.
    """
    parts = [d.get("model", ""), d.get("http_server", ""), d.get("upnp_xml_hash", "")]
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:16]


def log_event(db, mac, etype, confidence, detail):
    db.execute("INSERT INTO events (mac, ts, type, confidence, detail) VALUES (?,?,?,?,?)",
               (mac, time.time(), etype, confidence, detail))
    return (etype, confidence, detail)


def track_changes(db, d):
    """Compare one device to its history; store a snapshot only if something changed."""
    now, mac = time.time(), d["mac"]
    fw_new = d.get("firmware_version") or None
    fp_new = fingerprint(d)
    events, changed = [], False

    prev = db.execute(
        "SELECT firmware, fingerprint FROM snapshots WHERE mac=? ORDER BY id DESC LIMIT 1",
        (mac,)).fetchone()

    if prev is None:
        events.append(log_event(db, mac, "NEW DEVICE", "high",
                                f"First time seen. Firmware: {fw_new or 'unknown'}"))
        db.execute("INSERT OR IGNORE INTO devices VALUES (?,?,?)", (mac, now, now))
        changed = True
    else:
        fw_old, fp_old = prev
        db.execute("UPDATE devices SET last_seen=? WHERE mac=?", (now, mac))
        if fw_new and fw_old and fw_new != fw_old:
            if parse_version(fw_new) > parse_version(fw_old):
                events.append(log_event(db, mac, "FIRMWARE UPDATED", "high",
                                        f"{fw_old} -> {fw_new}"))
            else:
                events.append(log_event(db, mac, "FIRMWARE DOWNGRADED", "medium",
                                        f"{fw_old} -> {fw_new}"))
            changed = True
        elif fw_new and not fw_old:
            events.append(log_event(db, mac, "VERSION NOW DETECTED", "info",
                                    f"Firmware is {fw_new}"))
            changed = True
        elif not fw_new and fp_new != fp_old:
            events.append(log_event(db, mac, "POSSIBLE UPDATE", "low",
                                    "Device fingerprint changed; no version string to confirm."))
            changed = True

    if changed:
        db.execute("INSERT INTO snapshots (mac, ts, ip, vendor, model, firmware, fingerprint) "
                   "VALUES (?,?,?,?,?,?,?)",
                   (mac, now, d["ip"], d.get("vendor", ""), d.get("model", ""), fw_new, fp_new))
    return events


# ===================================== 5. CVE MATCH + PRIORITY SCORING
def find_db_entry(d, device_db):
    """Match a device to your curated DB. Keys look like 'vendor|model' (case-insensitive,
    and the vendor only has to appear inside the detected vendor string)."""
    models = {m.lower() for m in (d.get("model"), d.get("upnp_model_number")) if m}
    vendor = f"{d.get('vendor', '')} {d.get('upnp_manufacturer', '')}".lower()
    if not models:
        return None
    for key, entry in device_db.items():
        if "|" not in key:
            continue
        k_vendor, k_model = (s.strip().lower() for s in key.split("|", 1))
        if k_model in models and k_vendor in vendor:
            return entry
    return None


def matching_cves(d, entry):
    """CVEs from your DB that affect this device's CURRENT firmware.
    A CVE with no 'fixed_in' is treated as unfixed (affects every version)."""
    fw = d.get("firmware_version")
    if not fw or not entry:
        return []
    out = []
    for c in entry.get("cves", []):
        fixed = c.get("fixed_in")
        if fixed is None or parse_version(fw) < parse_version(fixed):
            out.append(c)
    return out


def load_kev():
    """CVE IDs that CISA says are exploited in the wild."""
    try:
        with urllib.request.urlopen(KEV_URL, timeout=10) as r:
            return {v["cveID"] for v in json.load(r).get("vulnerabilities", [])}
    except Exception as e:
        print(f"(warning: couldn't load CISA KEV feed: {e})")
        return set()


def load_epss(cve_ids):
    """{cve_id: probability of exploitation in the next 30 days (0-1)}."""
    if not cve_ids:
        return {}
    try:
        with urllib.request.urlopen(EPSS_URL + ",".join(cve_ids), timeout=10) as r:
            return {row["cve"]: float(row["epss"]) for row in json.load(r).get("data", [])}
    except Exception as e:
        print(f"(warning: couldn't load EPSS data: {e})")
        return {}


def score_update(ctx, cves, kev, epss, release_notes=""):
    """0-100 urgency score with plain-English reasons. See thresholds at the bottom."""
    score, reasons = 0, []

    # Exploitation (strongest signal)
    exploited = [c["id"] for c in cves if c["id"] in kev]
    if exploited:
        score += 40
        reasons.append(f"Actively exploited in the wild (CISA KEV): {', '.join(exploited)}")
    top_epss = max((epss.get(c["id"], 0) for c in cves), default=0)
    if top_epss >= 0.5:
        score += 20
        reasons.append(f"Very likely to be exploited soon (EPSS {top_epss:.0%})")
    elif top_epss >= 0.1:
        score += 10
        reasons.append(f"Moderate exploitation likelihood (EPSS {top_epss:.0%})")

    # Severity
    top_cvss = max((c.get("cvss", 0) for c in cves), default=0)
    if top_cvss >= 9:
        score += 25
        reasons.append(f"Critical severity (CVSS {top_cvss})")
    elif top_cvss >= 7:
        score += 15
        reasons.append(f"High severity (CVSS {top_cvss})")
    elif top_cvss >= 4:
        score += 7
        reasons.append(f"Medium severity (CVSS {top_cvss})")
    if any("AV:N" in c.get("vector", "") and "PR:N" in c.get("vector", "") for c in cves):
        score += 10
        reasons.append("Can be attacked over the network without logging in")

    # Reachability on YOUR network
    if ctx.get("upnp_exposed"):
        score += 20
        reasons.append("Device is reachable from the internet (UPnP port forwarding)")
    if ctx.get("default_creds"):
        score += 15
        reasons.append("Still using factory-default login")
    for port in ctx.get("open_ports", []):
        if port in RISKY_PORTS:
            score += 10
            reasons.append(f"Exposes {RISKY_PORTS[port]} (port {port})")
            break

    # Device role
    if ctx.get("role", "").lower() in HIGH_IMPACT_ROLES:
        score += 10
        reasons.append(f"High-impact device type ({ctx['role']})")

    # Vendor wording
    notes = release_notes.lower()
    if any(w in notes for w in ("security", "vulnerab", "cve-", "remote code")):
        score += 5
        reasons.append("Vendor release notes mention security fixes")

    if not cves and score < 20:
        reasons.append("No known vulnerabilities fixed by this update")

    score = min(score, 100)
    if score >= 70:
        tier, action = "CRITICAL", "Update today"
    elif score >= 45:
        tier, action = "HIGH", "Update this week"
    elif score >= 20:
        tier, action = "MEDIUM", "Update this month"
    else:
        tier, action = "LOW", "Update during routine maintenance"

    # End-of-life: an update can't fix it
    if ctx.get("eol") or ctx.get("fix_available") is False:
        if score >= 20:
            tier = "UNPATCHABLE"
            action = "No fix available - isolate on a guest network or replace the device"
        else:
            action = "Device is no longer supported - plan to replace it"
        reasons.append("Vendor no longer provides updates for this device")

    return {"score": score, "tier": tier, "action": action, "reasons": reasons}


# ============================================================== PIPELINE
def print_inventory(devices):
    print(f"\n{'IP':<16}{'MAC':<19}{'VENDOR':<26}{'MODEL':<16}{'FIRMWARE':<10}HOSTNAME")
    print("-" * 100)
    for d in devices:
        note = "  <- this machine" if d.get("is_this_machine") else ""
        print(f"{d['ip']:<16}{d['mac']:<19}{d.get('vendor', '')[:24]:<26}"
              f"{d.get('model', '-')[:14]:<16}{d.get('firmware_version', '-')[:9]:<10}"
              f"{d.get('hostname', '')}{note}")
    print(f"\n{len(devices)} device(s) found.")


def analyze(devices, db_path, device_db, offline):
    """Track changes, match CVEs, score priorities, print the report. Returns report data."""
    db = init_db(db_path)
    work = []
    for d in devices:
        if d.get("is_this_machine"):
            continue
        entry = find_db_entry(d, device_db)
        work.append((d, entry, matching_cves(d, entry)))

    # Only hit the web feeds if there is something to look up
    kev, epss = set(), {}
    cve_ids = sorted({c["id"] for _, _, cves in work for c in cves})
    if cve_ids and not offline:
        print("Fetching CISA KEV + EPSS data...")
        kev, epss = load_kev(), load_epss(cve_ids)

    changes, priorities, exposure, unknown_fw = [], [], [], []
    for d, entry, cves in work:
        name = f"{d.get('vendor', '?')} {d.get('model', '')}".strip()
        name = f"{name} ({d['ip']})"

        for etype, conf, detail in track_changes(db, d):
            changes.append((name, etype, conf, detail))

        if not d.get("firmware_version"):
            unknown_fw.append(name)
        for p in d.get("open_ports", []):
            if p in RISKY_PORTS:
                exposure.append(f"{name}: {RISKY_PORTS[p]} open on port {p}")

        entry = entry or {}
        latest = entry.get("latest_version")
        fw = d.get("firmware_version")
        avail = bool(fw and latest and parse_version(fw) < parse_version(latest))

        if cves or avail or entry.get("eol"):
            ctx = {
                "role": d.get("role") or entry.get("role", ""),
                "open_ports": d.get("open_ports", []),
                "upnp_exposed": d.get("upnp_exposed", False),
                "default_creds": d.get("default_creds", False),
                "eol": entry.get("eol", False),
                "fix_available": False if entry.get("eol") else None,
            }
            r = score_update(ctx, cves, kev, epss, entry.get("release_notes", ""))
            r.update({"device": name, "mac": d["mac"], "current": fw, "latest": latest,
                      "update_available": avail})
            priorities.append(r)
    db.commit()
    db.close()

    print("\n=== CHANGES SINCE LAST SCAN ===")
    if changes:
        for name, etype, conf, detail in changes:
            print(f"[{conf.upper():<6}] {etype}: {name} - {detail}")
    else:
        print("No changes.")

    print("\n=== UPDATE PRIORITIES (highest first) ===")
    if priorities:
        for r in sorted(priorities, key=lambda x: -x["score"]):
            print(f"\n[{r['tier']} {r['score']}/100] {r['device']}")
            ver = f"running {r['current']}" if r["current"] else "version unknown"
            if r["update_available"]:
                ver += f", latest known {r['latest']}"
            print(f"   Action: {r['action']}  ({ver})")
            for reason in r["reasons"]:
                print(f"   - {reason}")
    else:
        print("Nothing needs attention (or add devices to device_db.json to enable checks).")

    if exposure:
        print("\n=== EXPOSURE WARNINGS ===")
        for line in exposure:
            print(f"- {line}")
    if unknown_fw:
        print(f"\n{len(unknown_fw)} device(s) have no known firmware version, so update and CVE "
              f"checks were skipped for them.\nAdd model/firmware_version to "
              f"{OVERRIDES_FILE} to include them.")
    return priorities


# ================================================================ DEMO
DEMO_DEVICE_DB = {  # illustrative values, not verified vendor data
    "tp-link|Archer AX21": {
        "role": "router", "latest_version": "1.1.4",
        "release_notes": "Security update: fixes remote command injection.",
        "cves": [{"id": "CVE-2023-1389", "cvss": 8.8, "fixed_in": "1.1.4",
                  "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}]},
    "hikvision|DS-2CD2xx": {
        "role": "camera", "eol": True, "latest_version": "5.4.0",
        "cves": [{"id": "CVE-2021-36260", "cvss": 9.8,
                  "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"}]},
    "tp-link|KP125": {"role": "plug", "latest_version": "1.0.5", "cves": []},
}


def demo_devices(router_fw):
    base = {"randomized_mac": False, "is_this_machine": False, "discovery_method": "demo"}
    return [
        {**base, "ip": "192.168.1.1", "mac": "aa:bb:cc:00:00:01", "vendor": "TP-Link Systems Inc",
         "hostname": "router", "model": "Archer AX21", "firmware_version": router_fw,
         "open_ports": [80, 443], "upnp_exposed": True, "http_server": "demo-httpd/1.0"},
        {**base, "ip": "192.168.1.20", "mac": "aa:bb:cc:00:00:02", "vendor": "Hikvision",
         "hostname": "frontdoor-cam", "model": "DS-2CD2xx", "firmware_version": "5.4.0",
         "open_ports": [80, 554], "default_creds": True},
        {**base, "ip": "192.168.1.30", "mac": "aa:bb:cc:00:00:03", "vendor": "TP-Link Systems Inc",
         "hostname": "kasa-plug", "model": "KP125", "firmware_version": "1.0.5",
         "open_ports": []},
        {**base, "ip": "192.168.1.40", "mac": "aa:bb:cc:00:00:04", "vendor": "Unknown",
         "hostname": "mystery-device", "open_ports": [23]},
    ]


def run_demo(offline):
    if os.path.exists(DEMO_DB):
        os.remove(DEMO_DB)
    for title, fw in (("FIRST SCAN (router on old firmware)", "1.1.3"),
                      ("SECOND SCAN (router has since been updated)", "1.1.4")):
        print(f"\n{'#' * 70}\n# DEMO - {title}\n{'#' * 70}")
        devices = demo_devices(fw)
        print_inventory(devices)
        analyze(devices, DEMO_DB, DEMO_DEVICE_DB, offline)


# ================================================================ MAIN
STARTER_OVERRIDES = {
    "aa:bb:cc:dd:ee:ff": {
        "_note": "EXAMPLE - replace the MAC and delete this note. Any field here is merged "
                 "into the scan result for that device.",
        "vendor": "TP-Link", "model": "KP125", "firmware_version": "1.0.3",
        "role": "plug", "upnp_exposed": False, "default_creds": False}
}
STARTER_DEVICE_DB = {
    "EXAMPLE-VENDOR|EXAMPLE-MODEL": {
        "role": "camera", "latest_version": "2.0.1", "eol": False,
        "release_notes": "Paste the vendor's changelog text here.",
        "cves": [{"id": "CVE-0000-00000", "cvss": 7.5, "fixed_in": "2.0.0",
                  "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"}]}
}


def create_starter_files():
    for path, content in ((OVERRIDES_FILE, STARTER_OVERRIDES), (DEVICE_DB_FILE, STARTER_DEVICE_DB)):
        if not os.path.exists(path):
            save_json(path, content)
            print(f"Created starter file: {path}")


def main():
    ap = argparse.ArgumentParser(description="Home network device scanner + update priority tool")
    ap.add_argument("--offline", action="store_true", help="skip all web lookups")
    ap.add_argument("--skip-ports", action="store_true", help="skip port/HTTP probing")
    ap.add_argument("--skip-upnp", action="store_true", help="skip UPnP/SSDP discovery")
    ap.add_argument("--demo", action="store_true", help="run on built-in sample data")
    args = ap.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    if args.demo:
        run_demo(args.offline)
        return

    create_starter_files()
    devices = scan_network()
    if not devices:
        print("No devices found. Check you're on the network you intended to scan.")
        return

    devices = add_identity(devices, args.offline)
    if not args.skip_upnp:
        enrich_with_upnp(devices, get_local_ip())  # before overrides, so overrides win
    apply_overrides(devices)
    guess_roles(devices)
    if not args.skip_ports:
        probe_devices(devices)

    save_json(SCAN_FILE, devices)
    print_inventory(devices)
    analyze(devices, HISTORY_DB, load_json(DEVICE_DB_FILE, {}), args.offline)


if __name__ == "__main__":
    main()
