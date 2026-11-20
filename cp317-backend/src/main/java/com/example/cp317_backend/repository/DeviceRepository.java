package com.example.cp317_backend.repository;

import com.example.cp317_backend.domain.entity.Device;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface DeviceRepository extends JpaRepository<Device, UUID> {

}