package com.devtiro.task.mapper;

import com.devtiro.task.domain.CreateDeviceRequest;
import com.devtiro.task.domain.ModifyDeviceRequest;
import com.devtiro.task.domain.dto.*;
import com.devtiro.task.domain.entity.Device;
import jakarta.validation.Valid;

public interface DeviceMapper {

    CreateDeviceRequest fromDto(CreateDeviceRequestDto dto);

    ModifyDeviceRequest fromDto(ModifyDeviceRequestDto dto);

    DeviceDto toDto(Device device);

}
