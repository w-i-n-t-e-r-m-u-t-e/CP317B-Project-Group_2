package com.devtiro.task.exception;

public class DuplicateDeviceException extends RuntimeException {

    public DuplicateDeviceException() {
        super("A device with this name and IP already exists");
    }
}
