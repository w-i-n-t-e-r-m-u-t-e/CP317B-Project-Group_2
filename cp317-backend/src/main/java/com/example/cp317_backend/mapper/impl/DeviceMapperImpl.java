package com.example.cp317_backend.mapper.impl;

import com.example.cp317_backend.domain.CreateDeviceRequest;
import com.example.cp317_backend.domain.ModifyDeviceRequest;
import com.example.cp317_backend.domain.dto.*;
import com.example.cp317_backend.domain.entity.Device;
import com.example.cp317_backend.mapper.DeviceMapper;

@Component
public class DeviceMapperImpl implements DeviceMapper {
    @Override
    public CreateDeviceRequest fromDto(CreateDeviceRequestDto dto) {
        return new CreateDeviceRequest(dto.Device_Name(),
                                        dto.IP(),
                                        dto.Device_Version());
    }


    @Override
    public ModifyDeviceRequest fromDto(ModifyDeviceRequestDto dto) {
        return null;
    }

    @Override
    public DeviceDto toDto(Device device) {
        return new DeviceDto(device.getIp(),
                                device.getDeviceName(),
                                device.getStatus(),
                                device.getDeviceVersion(),
                                device.getLastUpdate());
    }


}
