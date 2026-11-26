package com.devtiro.task.service.impl;

import com.devtiro.task.domain.CreateDeviceRequest;
import com.devtiro.task.domain.ModifyDeviceRequest;
import com.devtiro.task.domain.entity.Device;
import com.devtiro.task.domain.entity.DeviceStatus;
import com.devtiro.task.exception.DuplicateDeviceException;
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
        rejectDuplicate(request.ip(), request.deviceName(), request.mac(), null);
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

        device.setDeviceType(request.deviceType());
        device.setTrust(request.trust());
        device.setMac(request.mac());
        device.setOpenPorts(request.openPorts());

        return deviceRepository.save(device); // also returns task

    }

    /** Same name and IP is a duplicate, unless the hardware addresses show two different devices. */
    private void rejectDuplicate(String ip, String name, String mac, UUID self) {
        boolean duplicate = deviceRepository.findByIpAndDeviceName(ip, name).stream()
                .anyMatch(other -> !other.getId().equals(self)
                        && (mac == null || other.getMac() == null || mac.equals(other.getMac())));
        if (duplicate) {
            throw new DuplicateDeviceException();
        }
    }

    @Override
    public List<Device> listDevices() {
        return deviceRepository.findAll(Sort.by(Direction.ASC, "deviceName"));
    }

    @Override
    public Device modifyDevice(UUID deviceId, ModifyDeviceRequest deviceRequest) {
        Device device = deviceRepository.findById(deviceId).orElseThrow(() -> new TaskNotFoundException(deviceId));
        // an update that sends no hardware address keeps the saved one, so compare with that
        String mac = deviceRequest.mac() != null ? deviceRequest.mac() : device.getMac();
        rejectDuplicate(deviceRequest.ip(), deviceRequest.deviceName(), mac, deviceId);

        device.setDeviceName(deviceRequest.deviceName());
        device.setDeviceVersion(deviceRequest.deviceVersion());
        device.setIp(deviceRequest.ip());
        if (deviceRequest.deviceType() != null) { // leave the type alone if it was not sent
            device.setDeviceType(deviceRequest.deviceType());
        }
        if (deviceRequest.trust() != null) {
            device.setTrust(deviceRequest.trust());
        }
        if (deviceRequest.mac() != null) {
            device.setMac(deviceRequest.mac());
        }
        if (deviceRequest.openPorts() != null) {
            device.setOpenPorts(deviceRequest.openPorts());
        }
        device.setLastUpdate(LocalDate.ofInstant(Instant.now(), ZoneId.systemDefault()));

        return deviceRepository.save(device);
    }

    @Override
    public void deleteDevice(UUID deviceId) {
        deviceRepository.deleteById(deviceId);

    }
}
