"""Look for risky services on your own devices.

The port check is adapted from iot_monitor.py on the team's new_ipgrabber branch.
An open port is not proof of a problem; it is something worth checking.
"""
import socket
from concurrent.futures import ThreadPoolExecutor

RISKY = {
    23: ("Telnet", "An old login that sends passwords unprotected. Turn Telnet off in the device's settings."),
    21: ("FTP", "File sharing that sends passwords unprotected. Turn FTP off if you don't need it."),
    5900: ("screen sharing (VNC)", "Turn it off if you don't use it. If you do, give it a strong password."),
    554: ("a video stream", "Make sure the camera asks for a password and its software is up to date."),
}


def is_open(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=0.5):
            return True
    except OSError:
        return False


def open_ports(ip, ports=tuple(RISKY)):
    """The risky ports that accept connections, as text such as "21,23" ("" if none)."""
    with ThreadPoolExecutor(len(ports)) as pool:
        return ",".join(str(p) for p, up in zip(ports, pool.map(lambda p: is_open(ip, p), ports)) if up)


def explain(text):
    """[(service, advice)] for a saved "21,23" string."""
    return [RISKY[int(p)] for p in (text or "").split(",") if p and int(p) in RISKY]


if __name__ == "__main__":  # self-check, on this computer only: python -m utils.ports
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        assert open_ports("127.0.0.1", (port,)) == str(port)
    assert open_ports("127.0.0.1", (port,)) == ""
    assert explain("23")[0][0] == "Telnet" and explain("") == [] and explain(None) == []
    print("ok")
