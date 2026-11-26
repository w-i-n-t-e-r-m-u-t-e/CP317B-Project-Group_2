package com.devtiro.task.domain;

public record ModifyDeviceRequest(String deviceName,
                                  String ip,
                                  String deviceVersion,
                                  String deviceType,
                                  String trust,
                                  String mac,
                                  String openPorts) {
}


