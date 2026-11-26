"""Run on a device you manage: reports its name, IP, type and OS version to the backend.

    python agent.py                                  # backend on this computer
    python agent.py --server http://192.168.1.20:8080

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


def my_ip(server):
    """The address this computer uses to reach the server (or the local network)."""
    host = urlparse(server).hostname
    if host in ("localhost", "127.0.0.1"):
        host = "10.255.255.255"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((host, 8080))  # sends nothing
        return s.getsockname()[0]


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
    server = parser.parse_args().server
    if "://" not in server:
        server = "http://" + server
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
