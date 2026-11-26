"""Work out what, if anything, the user should do. No window code, so it can be checked alone."""


def attention(devices, statuses):
    """[(kind, device)] needing action, most urgent first.

    kind: 'stranger' (user does not recognise it), 'risk' (risky service open), 'new' (not reviewed yet),
    'unsupported' (no more security updates) or 'outdated'.
    """
    items = [("stranger", d) for d in devices if d["trust"] == "UNKNOWN"]
    items += [("risk", d) for d in devices if d["trust"] == "MINE" and d.get("openPorts")]
    items += [("new", d) for d in devices if not d["trust"]]
    # a guest's updates are not the user's job
    for kind, wanted in (("unsupported", "UNSUPPORTED"), ("outdated", "OUTDATED")):
        items += [(kind, d) for d, status in zip(devices, statuses) if status == wanted and d["trust"] == "MINE"]
    return items


def headline(devices, statuses):
    count = len(attention(devices, statuses))
    if not devices:
        return "Scan your network to see what is on it."
    if count:
        return f"{count} thing{'s need' if count > 1 else ' needs'} your attention"
    # never claim everything is safe when some versions could not be checked
    unchecked = sum(status == "UNKNOWN" and d["trust"] == "MINE" for d, status in zip(devices, statuses))
    if unchecked:
        return f"Nothing urgent. {unchecked} of your devices could not be checked for updates."
    return "Nothing needs your attention."


if __name__ == "__main__":  # self-check: python utils/attention.py
    device = lambda trust: {"trust": trust}
    devices = [device(None), device("UNKNOWN"), device("MINE"), device("GUEST")]
    statuses = ["UNKNOWN", "UNKNOWN", "OUTDATED", "OUTDATED"]
    assert [kind for kind, _ in attention(devices, statuses)] == ["stranger", "new", "outdated"]
    assert headline(devices, statuses) == "3 things need your attention"
    assert headline([device("MINE")], ["UPDATED"]) == "Nothing needs your attention."
    assert "could not be checked" in headline([device("MINE")], ["UNKNOWN"])
    risky = {"trust": "MINE", "openPorts": "23"}
    assert [k for k, _ in attention([risky], ["UNSUPPORTED"])] == ["risk", "unsupported"]
    print("ok")
