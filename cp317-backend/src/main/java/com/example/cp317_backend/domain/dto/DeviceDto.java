package com.example.cp317_backend.domain.dto;

import com.example.cp317_backend.domain.entity.DeviceStatus;

import java.time.LocalDate;

public record DeviceDto(String ip,
                        String deviceName,
                        DeviceStatus status,
                        String deviceVersion,
                        LocalDate lastUpdated) {
}
