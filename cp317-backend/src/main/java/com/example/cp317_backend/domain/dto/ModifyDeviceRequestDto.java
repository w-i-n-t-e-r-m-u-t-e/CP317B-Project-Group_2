package com.devtiro.task.domain.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import org.hibernate.validator.constraints.Length;

public record ModifyDeviceRequestDto(
        @NotBlank(message = ERROR_MESSAGE_TITLE_LENGTH)
        @Length(max= 25,message = ERROR_MESSAGE_TITLE_LENGTH)
        String Device_Name,
        @Length(max =30, message = ERROR_MESSAGE_DEVICE_IP_LENGTH)
        @NotNull
        String IP,
        @Length(max =30, message = ERROR_MESSAGE_DEVICE_VERSION_LENGTH)
        @NotNull
        String Device_Version) {

    private static final String ERROR_MESSAGE_TITLE_LENGTH = "Title must be between 1-25 characters";
    private static final String ERROR_MESSAGE_DEVICE_VERSION_LENGTH = "Device Version must be less than 30 characters";
    private static final String ERROR_MESSAGE_DEVICE_IP_LENGTH = "Device IP must be less than 30 characters";
}


