package com.devtiro.task.domain.dto;

import java.net.Inet6Address;

final class IpAddress {

    private static final String IPV4 = "((25[0-5]|2[0-4]\\d|1?\\d?\\d)\\.){3}(25[0-5]|2[0-4]\\d|1?\\d?\\d)";

    private IpAddress() {
    }

    /** True for an IPv4 or IPv6 address. */
    static boolean isValid(String ip) {
        if (ip.matches(IPV4)) {
            return true;
        }
        if (!ip.matches("[0-9a-fA-F:.]+") || !ip.contains(":")) {
            return false;
        }
        try {
            Inet6Address.ofLiteral(ip); // checks the format only, no network lookup
            return true;
        } catch (IllegalArgumentException e) {
            return false;
        }
    }
}
