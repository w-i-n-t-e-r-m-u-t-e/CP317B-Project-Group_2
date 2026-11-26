"""What the scan needs to know about the computer the app is running on."""
import platform
import socket


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


def my_ip():
    """This computer's address: IPv4 on a normal network, IPv6 on an IPv6-only one."""
    try:
        ip = address_towards("10.255.255.255", socket.AF_INET)
    except OSError:
        ip = None
    # 192.0.0.x is a stand-in used on IPv6-only mobile networks, not a real address
    if ip is None or ip.startswith("192.0.0."):
        return address_towards("2001:4860:4860::8888", socket.AF_INET6)
    return ip


def find_entry(devices, name, ip, kind):
    """The saved entry that is this computer, or None.

    IPs get reused, so an IP alone only matches an entry that has no type yet.
    ponytail: two computers with the same name and type would share an entry; store a machine id if that happens
    """
    return (
        # same name and address: this entry, even if a scan saved it without a type
        next((d for d in devices if d["deviceName"] == name and d["ip"] == ip), None)
        # same name and type at an old address
        or next((d for d in devices if d["deviceName"] == name and d["deviceType"] == kind), None)
        or next((d for d in devices if d["ip"] == ip and not d["deviceType"]), None))
