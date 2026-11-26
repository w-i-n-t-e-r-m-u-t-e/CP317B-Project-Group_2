"""Decide whether a device's version is behind the latest one."""
import re


def parse(version):
    """'v1.10.0' -> [1, 10]; text without numbers -> []."""
    numbers = [int(n) for n in re.findall(r"\d+", version or "")]
    while len(numbers) > 1 and numbers[-1] == 0:  # so 2 and 2.0 are equal
        numbers.pop()
    return numbers


def status_of(version, latest):
    # ponytail: compares numbers only ("1.0-beta" counts as newer than "1.0")
    if not parse(version) or not parse(latest):
        return "UNKNOWN"
    return "OUTDATED" if parse(version) < parse(latest) else "UPDATED"


if __name__ == "__main__":  # self-check: python utils/version.py
    assert status_of("1.9", "1.10") == "OUTDATED"
    assert status_of("2", "2.0") == "UPDATED"
    assert status_of("v2.1", "2.0") == "UPDATED"
    assert status_of("unknown", "2.0") == "UNKNOWN"
    assert status_of("1.0", "") == "UNKNOWN"
    print("ok")
