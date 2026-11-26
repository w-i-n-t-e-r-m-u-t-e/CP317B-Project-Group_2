"""Find devices on the local network and register the new ones with the backend."""
import json
import platform
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen
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


def find_devices():
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


def scan():
    """Scan, add new devices, name the unnamed ones, and return (found, added)."""
    with urlopen(API_URL, timeout=3) as response:
        known = {device["ip"]: device for device in json.load(response)}
    found = find_devices()
    # look up new devices, and saved ones whose name is still just the IP
    lookup = [ip for ip in found if ip not in known or known[ip]["deviceName"] == ip]
    with ThreadPoolExecutor(64) as pool:
        names = dict(zip(lookup, pool.map(hostname, lookup)))
    macs = mac_table()  # filled in by the pings above
    # no name from the device: show its maker instead
    names = {ip: label(ip, macs.get(ip)) if name == ip else name for ip, name in names.items()}
    added = 0
    for ip, name in names.items():
        try:
            if ip not in known:
                # a ping cannot tell us the software version
                save({"Device_Name": name, "IP": ip, "Device_Version": "unknown"})
                added += 1
            elif name != ip:
                save({"Device_Name": name, "IP": ip, "Device_Version": known[ip]["deviceVersion"]},
                     known[ip]["id"])
        except HTTPError:
            continue  # the backend rejected this one; keep saving the others
    return len(found), added
