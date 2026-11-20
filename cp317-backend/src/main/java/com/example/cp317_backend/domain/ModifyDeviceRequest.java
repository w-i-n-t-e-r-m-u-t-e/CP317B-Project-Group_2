package com.example.cp317_backend.domain;

public record ModifyDeviceRequest(String deviceName,
                                  String ip,
                                  String deviceVersion) {
}


