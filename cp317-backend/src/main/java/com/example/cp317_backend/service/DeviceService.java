package com.example.cp317_backend.service;

import com.example.cp317_backend.domain.CreateDeviceRequest;
import com.example.cp317_backend.domain.ModifyDeviceRequest;
import com.example.cp317_backend.domain.entity.Device;

import java.util.List;
import java.util.UUID;

public interface DeviceService {

    Device createDevice (CreateDeviceRequest request);

    List<Device> listDevices();

    Device modifyDevice(UUID DeviceId, ModifyDeviceRequest DeviceRequest);

    void deleteDevice(UUID DeviceId);
}
