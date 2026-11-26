package com.devtiro.task.domain.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import org.hibernate.validator.constraints.Length;

public record ModifyDeviceRequestDto(
        @NotBlank(message = ERROR_MESSAGE_TITLE_LENGTH)
        @Length(max= 25,message = ERROR_MESSAGE_TITLE_LENGTH)
        String Device_Name,
        @Length(max =30, message = ERROR_MESSAGE_DEVICE_IP_LENGTH)
        @NotBlank(message = "Device IP is required")
        @Pattern(regexp = "^$|((25[0-5]|2[0-4]\\d|1?\\d?\\d)\\.){3}(25[0-5]|2[0-4]\\d|1?\\d?\\d)",
                message = "Device IP must look like 192.168.1.10")
        String IP,
        @Length(max =30, message = ERROR_MESSAGE_DEVICE_VERSION_LENGTH)
        @NotBlank(message = "Device Version is required")
        String Device_Version,
        @Length(max = 30, message = "Device Type must be less than 30 characters")
        String Device_Type) {

    private static final String ERROR_MESSAGE_TITLE_LENGTH = "Title must be between 1-25 characters";
    private static final String ERROR_MESSAGE_DEVICE_VERSION_LENGTH = "Device Version must be less than 30 characters";
    private static final String ERROR_MESSAGE_DEVICE_IP_LENGTH = "Device IP must be less than 30 characters";
}


