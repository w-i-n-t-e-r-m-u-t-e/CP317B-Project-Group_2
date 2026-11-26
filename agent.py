"""Run on a device you manage: reports its name, IP, type and OS version to the backend.

    python agent.py                                  # backend on this computer
    python agent.py --server http://192.168.1.20:8080
    python agent.py --server "http://[2001:db8::5]:8080"   # IPv6 needs the brackets

Needs only Python, so this one file can be copied to other computers.
"""
import argparse
import json
import platform
import socket
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def os_info():
    """(type, version) of this computer."""
    system = platform.system()
    if system == "Darwin":
        return "macOS", platform.mac_ver()[0]
    if system == "Windows":
        return "Windows", platform.version()  # build number, e.g. 10.0.26100
    try:
        release = platform.freedesktop_os_release()
        return release.get("NAME", system)[:30], release.get("VERSION_ID", platform.release())
    except (OSError, AttributeError):
        return system, platform.release()


def address_towards(host, family):
    """The address this computer would use to reach host. Sends nothing."""
    with socket.socket(family, socket.SOCK_DGRAM) as s:
        s.connect((host, 8080))
        return s.getsockname()[0]


def my_ip(server):
    """This computer's address: IPv4 on a normal network, IPv6 on an IPv6-only one."""
    host = urlparse(server).hostname
    if host not in ("localhost", "127.0.0.1", "::1") and ":" in host:
        return address_towards(host, socket.AF_INET6)
    if host in ("localhost", "127.0.0.1", "::1") or host.endswith(".local"):
        host = "10.255.255.255"
    try:
        ip = address_towards(host, socket.AF_INET)
    except OSError:
        ip = None
    # 192.0.0.x is a stand-in used on IPv6-only mobile networks, not a real address
    if ip is None or ip.startswith("192.0.0."):
        return address_towards("2001:4860:4860::8888", socket.AF_INET6)
    return ip


def find_entry(devices, name, ip, kind):
    """The saved entry that is this computer, or None.

    IPs get reused, so an IP alone only matches an entry no agent has claimed (it has no type).
    ponytail: two computers with the same name and type would share an entry; store a machine id if that happens
    """
    return (
        # same name and address: this entry, even if a scan saved it without a type
        next((d for d in devices if d["deviceName"] == name and d["ip"] == ip), None)
        # same name and type at an old address
        or next((d for d in devices if d["deviceName"] == name and d["deviceType"] == kind), None)
        or next((d for d in devices if d["ip"] == ip and not d["deviceType"]), None))


def report(server, name, ip, kind, version):
    """Update this device's entry, or create it. Returns 'added' or 'updated'."""
    url = server.rstrip("/") + "/api/v1/devices"
    with urlopen(url, timeout=5) as response:
        devices = json.load(response)
    match = find_entry(devices, name, ip, kind)
    body = {"Device_Name": name, "IP": ip, "Device_Version": version, "Device_Type": kind}
    request = Request(f"{url}/{match['id']}" if match else url, json.dumps(body).encode(),
                      {"Content-Type": "application/json"}, method="PUT" if match else "POST")
    urlopen(request, timeout=5).close()
    return "updated" if match else "added"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Report this device to the backend.")
    parser.add_argument("--server", default="http://localhost:8080")
    args = parser.parse_args()
    server = args.server if "://" in args.server else "http://" + args.server
    name = platform.node().removesuffix(".local")[:25] or "unnamed"
    kind, version = os_info()

    try:
        ip = my_ip(server)
        result = report(server, name, ip, kind, version)
    except HTTPError as error:
        raise SystemExit(f"The backend refused the report: {error}")
    except OSError as error:
        raise SystemExit(f"Could not reach {server}: {error}")
    print(f"{result}: {name} ({ip}) {kind} {version}")
