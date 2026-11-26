package com.devtiro.task.mapper.impl;

import com.devtiro.task.domain.CreateDeviceRequest;
import com.devtiro.task.domain.ModifyDeviceRequest;
import com.devtiro.task.domain.dto.*;
import com.devtiro.task.domain.entity.Device;
import com.devtiro.task.mapper.DeviceMapper;

@org.springframework.stereotype.Component
public class DeviceMapperImpl implements DeviceMapper {
    @Override
    public CreateDeviceRequest fromDto(CreateDeviceRequestDto dto) {
        return new CreateDeviceRequest(dto.Device_Name(),
                                        dto.IP(),
                                        dto.Device_Version(),
                                        dto.Device_Type(),
                                        dto.Trust(),
                                        dto.Mac(),
                                        dto.Open_Ports());
    }


    @Override
    public ModifyDeviceRequest fromDto(ModifyDeviceRequestDto dto) {
        return new ModifyDeviceRequest(dto.Device_Name(),
                                        dto.IP(),
                                        dto.Device_Version(),
                                        dto.Device_Type(),
                                        dto.Trust(),
                                        dto.Mac(),
                                        dto.Open_Ports());
    }

    @Override
    public DeviceDto toDto(Device device) {
        return new DeviceDto(device.getId(),
                                device.getIp(),
                                device.getDeviceName(),
                                device.getStatus(),
                                device.getDeviceVersion(),
                                device.getDeviceType(),
                                device.getTrust(),
                                device.getMac(),
                                device.getOpenPorts(),
                                device.getLastUpdate());
    }


}
