package com.devtiro.task.service.impl;

import com.devtiro.task.domain.CreateDeviceRequest;
import com.devtiro.task.domain.ModifyDeviceRequest;
import com.devtiro.task.domain.entity.Device;
import com.devtiro.task.domain.entity.DeviceStatus;
import com.devtiro.task.exception.TaskNotFoundException;
import com.devtiro.task.repository.DeviceRepository;
import com.devtiro.task.service.DeviceService;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.data.domain.Sort.Direction;
import java.time.Instant;
import java.time.ZoneId;
import java.util.List;
import java.util.UUID;
import java.time.LocalDate;


@Service
public class DeviceServiceImpl implements DeviceService {

    private final DeviceRepository deviceRepository;

    public DeviceServiceImpl(DeviceRepository deviceRepository){
        this.deviceRepository = deviceRepository;
    }

    @Override
    public Device createDevice(CreateDeviceRequest request) {
        Instant now = Instant.now();
        Device device = new Device(
                null,
                request.ip(),
                request.deviceName(),
                DeviceStatus.UPDATED,
                request.deviceVersion(),
                now,
                null
                );

        return deviceRepository.save(device); // also returns task

    }

    @Override
    public List<Device> listDevices() {
        return deviceRepository.findAll(Sort.by(Direction.ASC, "Device_name"));
    }

    @Override
    public Device modifyDevice(UUID deviceId, ModifyDeviceRequest deviceRequest) {
        Device device = deviceRepository.findById(deviceId).orElseThrow(() -> new TaskNotFoundException(deviceId));

        device.setDeviceName(deviceRequest.deviceName());
        device.setDeviceVersion(deviceRequest.deviceVersion());
        device.setIp(deviceRequest.ip());
        device.setLastUpdate(LocalDate.ofInstant(Instant.now(), ZoneId.systemDefault()));

        return deviceRepository.save(device);
    }

    @Override
    public void deleteDevice(UUID deviceId) {
        deviceRepository.deleteById(deviceId);

    }
}
