package com.devtiro.task.repository;

import com.devtiro.task.domain.entity.Device;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface DeviceRepository extends JpaRepository<Device, UUID> {

    boolean existsByIpAndDeviceName(String ip, String deviceName);

    boolean existsByIpAndDeviceNameAndIdNot(String ip, String deviceName, UUID id);

}