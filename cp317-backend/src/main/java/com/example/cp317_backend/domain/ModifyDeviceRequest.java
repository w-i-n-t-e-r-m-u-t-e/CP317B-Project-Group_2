package com.devtiro.task.domain;

public record ModifyDeviceRequest(String deviceName,
                                  String ip,
                                  String deviceVersion) {
}


