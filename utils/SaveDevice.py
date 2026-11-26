from pathlib import Path

from schema.schema import Device, DeviceList


class SaveDevice:
    def __init__(self, file_path: str | Path | None = None):
        self.file_path = (
            Path(file_path)
            if file_path is not None
            else Path(__file__).resolve().parent / "devices.json"
        )
        self.device_list = self._load_device_list()

    def add_device(self, device: Device) -> bool:
        if any(
            existing.device_id == device.device_id
            for existing in self.device_list.devices
        ):
            return False

        updated_device_list = DeviceList(devices=[*self.device_list.devices, device])
        self._write_device_list(updated_device_list)
        self.device_list = updated_device_list
        return True

    def get_devices(self) -> DeviceList:
        return self.device_list

    def save_to_json(self) -> None:
        self._write_device_list(self.device_list)

    def _load_device_list(self) -> DeviceList:
        if not self.file_path.exists():
            return DeviceList()

        json_data = self.file_path.read_text(encoding="utf-8")
        if not json_data.strip():
            return DeviceList()
        return DeviceList.model_validate_json(json_data)

    def _write_device_list(self, device_list: DeviceList) -> None:
        self.file_path.write_text(
            device_list.model_dump_json(indent=2),
            encoding="utf-8",
        )