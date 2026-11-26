package com.devtiro.task.domain.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.AssertTrue;
import org.hibernate.validator.constraints.Length;

public record ModifyDeviceRequestDto(
        @NotBlank(message = ERROR_MESSAGE_TITLE_LENGTH)
        @Length(max= 25,message = ERROR_MESSAGE_TITLE_LENGTH)
        String Device_Name,
        @Length(max = 45, message = ERROR_MESSAGE_DEVICE_IP_LENGTH)
        @NotBlank(message = "Device IP is required")
        String IP,
        @Length(max =30, message = ERROR_MESSAGE_DEVICE_VERSION_LENGTH)
        @NotBlank(message = "Device Version is required")
        String Device_Version,
        @Length(max = 30, message = "Device Type must be less than 30 characters")
        String Device_Type,
        @Pattern(regexp = "MINE|GUEST|UNKNOWN", message = "Trust must be MINE, GUEST or UNKNOWN")
        String Trust,
        @Pattern(regexp = "[0-9A-F]{12}", message = "MAC must be 12 hex digits")
        String Mac,
        @Pattern(regexp = "(\\d{1,5}(,\\d{1,5})*)?", message = "Open ports must look like 21,23")
        String Open_Ports) {

    private static final String ERROR_MESSAGE_TITLE_LENGTH = "Title must be between 1-25 characters";
    private static final String ERROR_MESSAGE_DEVICE_VERSION_LENGTH = "Device Version must be less than 30 characters";
    private static final String ERROR_MESSAGE_DEVICE_IP_LENGTH = "Device IP must be 45 characters or less";

    @AssertTrue(message = "Device IP must be an IPv4 or IPv6 address")
    public boolean isIpValid() {
        return IP == null || IP.isBlank() || IpAddress.isValid(IP);
    }
}
