package com.devtiro.task.domain;

public record CreateDeviceRequest(String deviceName,
                                  String ip,
                                  String deviceVersion) {

}