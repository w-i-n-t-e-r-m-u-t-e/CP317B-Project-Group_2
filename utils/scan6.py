"""Find neighbours on an IPv6-only network (macOS and Linux)."""
import platform
import re
import subprocess


def run(*command):
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=10).stdout
    except subprocess.TimeoutExpired as error:
        out = error.stdout or ""
        return out.decode(errors="replace") if isinstance(out, bytes) else out


def interface():
    """Name of the network interface in use, such as 'en0'."""
    if platform.system() == "Darwin":
        match = re.search(r"interface: (\S+)", run("route", "-n", "get", "-inet6", "default"))
    else:
        match = re.search(r" dev (\S+)", run("ip", "-6", "route", "show", "default"))
    if not match:
        raise OSError("no IPv6 network found")
    return match.group(1)


def parse_replies(text):
    """Link-local addresses that answered, from ping output."""
    return sorted(set(re.findall(r"from (fe80::[0-9a-f:]+)", text)))


def own_addresses():
    command = ("ifconfig",) if platform.system() == "Darwin" else ("ip", "-6", "addr")
    return set(re.findall(r"inet6 (fe80::[0-9a-f:]+)", run(*command)))


def find_neighbours():
    # ponytail: one multicast ping; devices that ignore it (often Windows) are missed
    if platform.system() == "Windows":
        raise OSError("scanning IPv6 is not supported on Windows")
    name = interface()
    ping = "ping6" if platform.system() == "Darwin" else "ping"
    replies = parse_replies(run(ping, "-c", "3", f"ff02::1%{name}"))
    return [ip for ip in replies if ip not in own_addresses()]


def neighbour_macs():
    """{ipv6 address: 'AABBCCDDEEFF'} for neighbours seen recently."""
    command = ("ndp", "-an") if platform.system() == "Darwin" else ("ip", "-6", "neigh")
    table = {}
    for line in run(*command).splitlines():
        match = re.match(r"(fe80::[0-9a-f:]+)\S*\s.*?\b((?:[0-9a-f]{1,2}:){5}[0-9a-f]{1,2})\b", line)
        if match:
            table[match.group(1)] = "".join(part.zfill(2) for part in match.group(2).split(":")).upper()
    return table


if __name__ == "__main__":  # self-check: python utils/scan6.py
    sample = "16 bytes from fe80::1%en0, icmp_seq=0\n64 bytes from fe80::2%eth0: icmp_seq=1\n16 bytes from fe80::1%en0"
    assert parse_replies(sample) == ["fe80::1", "fe80::2"]
    print("ok")
