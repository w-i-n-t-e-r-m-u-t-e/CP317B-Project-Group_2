package com.devtiro.task.domain.entity;

import jakarta.persistence.*;

import java.time.Instant;
import java.time.LocalDate;
import java.util.Objects;
import java.util.UUID;

import static org.springframework.data.jpa.domain.AbstractPersistable_.id;

@Entity
@Table(name = "Device")


public class Device {

    public Device(){

    }


    public Device(
            UUID id,
            String ip,
            String deviceName,
            DeviceStatus status,
            String deviceVersion,
            Instant created, // last updated is initially set to the date when device is added
            LocalDate updated
        ){

        this.id = id;
        this.ip = ip;
        this.deviceName = deviceName;
        this.status = status;
        this.deviceVersion = deviceVersion;
        this.created = created;
        this.lastUpdate = null;
    }

    @Id
    @Column(name = "ID", updatable = false, nullable = false)
    private UUID id;


    @Column(name = "IP", updatable = false, nullable = false)
    private String ip;

    @Column(name = "Device_name", updatable = true, nullable = false)
    private String deviceName;

    @Enumerated(EnumType.STRING)
    @Column(name = "Device_Status", nullable = false)
    private DeviceStatus status;

    @Column(name = "Device_Version", updatable = true, length =1000)
    private String deviceVersion;

    @Column(name = "Created", updatable = true, nullable = false)
    private Instant created;

    @Column(name = "Last_Update", updatable = true, nullable = true)
    private LocalDate lastUpdate;







    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getIp() {
        return ip;
    }

    public void setIp(String ip) {
        this.ip = ip;
    }

    public String getDeviceName() {
        return deviceName;
    }

    public void setDeviceName(String deviceName) {
        this.deviceName = deviceName;
    }

    public DeviceStatus getStatus() {
        return status;
    }

    public void setStatus(DeviceStatus status) {
        this.status = status;
    }

    public String getDeviceVersion() {
        return deviceVersion;
    }

    public void setDeviceVersion(String deviceVersion) {
        this.deviceVersion = deviceVersion;
    }

    public Instant getCreated() {return created;}

    public void setCreated(Instant created) {this.created = created;}

    public LocalDate getLastUpdate() {
        return lastUpdate;
    }

    public void setLastUpdate(LocalDate lastUpdate) {this.lastUpdate = lastUpdate;}











}
