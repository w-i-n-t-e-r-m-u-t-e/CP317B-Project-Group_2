package com.example.cp317_backend.domain;

public record CreateDeviceRequest(String deviceName,
                                  String ip,
                                  String deviceVersion) {

}