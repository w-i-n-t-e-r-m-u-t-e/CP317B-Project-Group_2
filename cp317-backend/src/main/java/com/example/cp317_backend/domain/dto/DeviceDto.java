package com.devtiro.task.domain.dto;

import com.devtiro.task.domain.entity.DeviceStatus;

import java.time.LocalDate;
import java.util.UUID;

public record DeviceDto(UUID id,
                        String ip,
                        String deviceName,
                        DeviceStatus status,
                        String deviceVersion,
                        String deviceType,
                        String trust,
                        String mac,
                        String openPorts,
                        LocalDate lastUpdated) {
}
