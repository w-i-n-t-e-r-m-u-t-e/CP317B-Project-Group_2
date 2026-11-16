package com.devtiro.task.domain.dto;

import com.devtiro.task.domain.entity.DeviceStatus;

import java.time.LocalDate;

public record DeviceDto(String ip,
                        String deviceName,
                        DeviceStatus status,
                        String deviceVersion,
                        LocalDate lastUpdated) {
}
