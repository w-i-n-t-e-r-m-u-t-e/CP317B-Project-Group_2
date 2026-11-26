"""Find devices on the local network and register the new ones with the backend."""
import json
import platform
import socket
import subprocess
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from utils.ports import open_ports
from utils.scan6 import find_neighbours, interface, neighbour_macs
from utils.this_computer import find_entry, my_ip, os_info
from utils.vendor import label, mac_table

API_URL = "http://localhost:8080/api/v1/devices"


def local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("10.255.255.255", 1))  # sends nothing, just picks the network interface
        return s.getsockname()[0]


def ping(ip):
    count = "-n" if platform.system() == "Windows" else "-c"
    try:
        out = subprocess.run(["ping", count, "1", ip], capture_output=True, timeout=1).stdout
    except subprocess.TimeoutExpired:
        return False
    return b"ttl=" in out.lower()  # Windows exits 0 even for "unreachable"


def ipv6_only():
    """True when there is no real IPv4 network, as on some phone hotspots."""
    try:
        return local_ip().startswith("192.0.0.")
    except OSError:
        return True


def find_devices():
    if ipv6_only():
        return find_neighbours()
    # ponytail: assumes a /24 network (254 addresses), read the real netmask if yours is bigger
    prefix = local_ip().rsplit(".", 1)[0]
    ips = [f"{prefix}.{n}" for n in range(1, 255)]
    with ThreadPoolExecutor(64) as pool:
        return [ip for ip, up in zip(ips, pool.map(ping, ips)) if up]


def read_name(data, pos):
    """Read a DNS name starting at pos; return (name, position after it)."""
    labels = []
    end = None
    for _ in range(64):  # a bad reply could otherwise loop forever
        length = data[pos]
        if length >= 0xC0:  # pointer to a name earlier in the packet
            end = end or pos + 2
            pos = (length & 0x3F) << 8 | data[pos + 1]
        elif length:
            labels.append(data[pos + 1:pos + 1 + length].decode(errors="replace"))
            pos += 1 + length
        else:
            return ".".join(labels), end or pos + 1
    raise ValueError("bad name")


def mdns_name(ip, port=5353):
    """Ask the device itself for its name (Bonjour/mDNS). Returns None if it does not answer."""
    reverse = ".".join(reversed(ip.split("."))) + ".in-addr.arpa"
    question = b"".join(bytes([len(part)]) + part.encode() for part in reverse.split("."))
    query = bytes([0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]) + question + bytes([0, 0, 12, 0, 1])  # PTR
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1)
            sock.connect((ip, port))  # only accept replies from that device
            sock.send(query)
            data = sock.recv(1500)
        pos = 12
        for _ in range(int.from_bytes(data[4:6], "big")):  # skip the echoed question
            pos = read_name(data, pos)[1] + 4
        if int.from_bytes(data[6:8], "big"):  # has an answer
            pos = read_name(data, pos)[1]
            if data[pos:pos + 2] == bytes([0, 12]):
                return read_name(data, pos + 10)[0]
    except (OSError, IndexError, ValueError):
        pass
    return None


def hostname(ip):
    """Best name we can find for a device, or its IP."""
    if ":" in ip:
        return ip  # no name lookup for IPv6; scan() builds a short name instead
    try:
        name = socket.gethostbyaddr(ip)[0]
    except OSError:
        name = mdns_name(ip) or ip
    return name.removesuffix(".local")[:25].strip() or ip  # backend limit is 25 characters


def save(body, device_id=None):
    url = f"{API_URL}/{device_id}" if device_id else API_URL
    request = Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"},
                      method="PUT" if device_id else "POST")
    urlopen(request, timeout=3).close()


def match(devices, ip, mac):
    """The saved entry for a device seen at this IP with this hardware address, or None."""
    if mac:
        for device in devices:
            if device["mac"] == mac:
                return device  # same hardware, even if its IP changed
    # by IP, unless the hardware address shows that someone else now has that IP
    return next((d for d in devices if d["ip"] == ip and (not mac or not d["mac"] or d["mac"] == mac)), None)


def register_this_computer():
    """Fill in this computer's type and version, which no network scan could find out."""
    with urlopen(API_URL, timeout=3) as response:
        devices = json.load(response)
    name = platform.node().removesuffix(".local")[:25] or "This computer"
    kind, version = os_info()
    ip = my_ip()
    node = uuid.getnode()
    # getnode() makes up a number (marked by this bit) when it cannot read a hardware address
    mac = None if node >> 40 & 1 else f"{node:012X}"
    entry = (next((d for d in devices if mac and d["mac"] == mac), None)
             or find_entry(devices, name, ip, kind))
    body = {"Device_Name": entry["deviceName"] if entry else name,  # keep a name the user chose
            "IP": ip, "Device_Version": version, "Device_Type": kind, "Mac": mac}
    if not entry or not entry["trust"]:
        body["Trust"] = "MINE"  # the app is running on it
    save(body, entry["id"] if entry else None)


def scan():
    """Scan, add new devices, update known ones, and return (found, added)."""
    try:
        register_this_computer()
    except HTTPError:
        pass  # rejected, for example as a duplicate; carry on with the scan
    with urlopen(API_URL, timeout=3) as response:
        devices = json.load(response)
    found = find_devices()
    # filled in by the pings above
    macs = neighbour_macs() if any(":" in ip for ip in found) else mac_table()
    # one address answering for several IPs is a router or hotspot, so it identifies nothing
    counts = Counter(macs.get(ip) for ip in found)
    macs = {ip: macs[ip] for ip in found if ip in macs and counts[macs[ip]] == 1}
    # this computer is already registered; its address on the network can differ from the one it reports
    own = my_ip()
    entries = {ip: match(devices, ip, macs.get(ip)) for ip in found if ip != own}
    # look up names for new devices, and for saved ones still named after their IP
    lookup = [ip for ip, entry in entries.items() if not entry or entry["deviceName"] == entry["ip"]]
    with ThreadPoolExecutor(64) as pool:
        names = dict(zip(lookup, pool.map(hostname, lookup)))
    added = 0
    for ip, entry in entries.items():
        mac = macs.get(ip)
        name = names.get(ip)
        if name == ip:  # the device gave no name: show its maker instead
            name = label(ip, mac)
            if name == ip and ":" in ip:  # a bare IPv6 address is too long to be a name
                name = f"Device (:{ip.rsplit(':', 1)[1]})"
        body = {"Device_Name": name or (entry or {}).get("deviceName"), "IP": ip,
                "Device_Version": entry["deviceVersion"] if entry else "unknown", "Mac": mac}
        try:
            if not entry:
                save(body)  # a ping cannot tell us the software version
                added += 1
            elif name not in (None, entry["deviceName"]) or entry["ip"] != ip or (mac and entry["mac"] != mac):
                save(body, entry["id"])
        except HTTPError:
            continue  # the backend rejected this one; keep saving the others
    check_safety(found)
    return len(found), added


def check_safety(found):
    """Check devices marked as the user's own, and only ones seen on this network just now."""
    here = set(found)
    try:
        here.add(my_ip())  # this computer
    except OSError:
        pass
    with urlopen(API_URL, timeout=3) as response:
        devices = json.load(response)
    for device in devices:
        ip = device["ip"]
        if device["trust"] != "MINE" or ip not in here:
            continue
        # a link-local IPv6 address also needs the interface name
        ports = open_ports(f"{ip}%{interface()}" if ip.startswith("fe80:") else ip)
        if ports != device["openPorts"]:
            try:
                save({"Device_Name": device["deviceName"], "IP": ip, "Device_Version": device["deviceVersion"],
                      "Open_Ports": ports}, device["id"])
            except HTTPError:
                continue
