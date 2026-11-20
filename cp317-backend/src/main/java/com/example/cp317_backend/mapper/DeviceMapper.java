package com.example.cp317_backend.mapper;

import com.example.cp317_backend.domain.CreateDeviceRequest;
import com.example.cp317_backend.domain.ModifyDeviceRequest;
import com.example.cp317_backend.domain.dto.*;
import com.example.cp317_backend.domain.entity.Device;
import jakarta.validation.Valid;

public interface DeviceMapper {

    CreateDeviceRequest fromDto(CreateDeviceRequestDto dto);

    ModifyDeviceRequest fromDto(ModifyDeviceRequestDto dto);

    DeviceDto toDto(Device device);

}
