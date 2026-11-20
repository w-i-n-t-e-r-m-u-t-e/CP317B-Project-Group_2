package com.example.cp317_backend.controller;

import com.example.cp317_backend.domain.CreateDeviceRequest;
import com.example.cp317_backend.domain.ModifyDeviceRequest;
import com.example.cp317_backend.domain.dto.CreateDeviceRequestDto;
import com.example.cp317_backend.domain.dto.DeviceDto;
import com.example.cp317_backend.domain.dto.ModifyDeviceRequestDto;
import com.example.cp317_backend.domain.entity.Device;
import com.example.cp317_backend.mapper.DeviceMapper;
import com.example.cp317_backend.service.DeviceService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping(path = "/api/v1/devices")
public class DeviceController {

    private final DeviceService deviceService;
    private final DeviceMapper deviceMapper;



    public DeviceController(DeviceService deviceService, DeviceMapper deviceMapper) {
        this.deviceService = deviceService;
        this.deviceMapper = deviceMapper;
    }
    @PostMapping
    public ResponseEntity<DeviceDto> createDevice(
            @Valid @RequestBody
            CreateDeviceRequestDto createDeviceRequestDto
    ){
        CreateDeviceRequest createDeviceRequest = deviceMapper.fromDto(createDeviceRequestDto);
        Device device = deviceService.createDevice(createDeviceRequest);
        DeviceDto createdDeviceDto = deviceMapper.toDto(device);
        return new ResponseEntity<>(createdDeviceDto, HttpStatus.CREATED);
    }

    @GetMapping
    public ResponseEntity<List<DeviceDto>> listDevices() {
        List<Device> devices = deviceService.listDevices();
        List<DeviceDto> deviceDtos = devices.stream().map(deviceMapper::toDto).toList();
        return ResponseEntity.ok(deviceDtos);

    }

    @PutMapping(path = "/{deviceId}")
    public ResponseEntity<DeviceDto> updateDevice(
            @PathVariable UUID deviceId,
            @Valid @RequestBody
            ModifyDeviceRequestDto modifyDeviceRequestDto
    ) {
        ModifyDeviceRequest modifyDeviceRequest = deviceMapper.fromDto(modifyDeviceRequestDto);
        Device device = deviceService.modifyDevice(deviceId, modifyDeviceRequest);
        DeviceDto modifiedDeviceDto = deviceMapper.toDto(device);
        return ResponseEntity.ok(modifiedDeviceDto);
    }

    @DeleteMapping(path = "/{deviceId}")
    public ResponseEntity<Void> deleteDevice(@PathVariable UUID deviceId) {
        deviceService.deleteDevice(deviceId);
        return new ResponseEntity<>(HttpStatus.NO_CONTENT);
    }

}
