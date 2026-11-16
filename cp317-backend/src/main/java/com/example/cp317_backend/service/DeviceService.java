package com.devtiro.task.service;

import com.devtiro.task.domain.CreateDeviceRequest;
import com.devtiro.task.domain.ModifyDeviceRequest;
import com.devtiro.task.domain.entity.Device;

import java.util.List;
import java.util.UUID;

public interface DeviceService {

    Device createDevice (CreateDeviceRequest request);

    List<Device> listDevices();

    Device modifyDevice(UUID DeviceId, ModifyDeviceRequest DeviceRequest);

    void deleteDevice(UUID DeviceId);
}
