from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import XiaoduDevice
from .const import DOMAIN
from .coordinator import XiaoduCoordinator


class XiaoduEntity(CoordinatorEntity[XiaoduCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: XiaoduCoordinator, device: XiaoduDevice, suffix: str) -> None:
        super().__init__(coordinator)
        self._device_key = device.key
        self._suffix = suffix
        self._attr_unique_id = f"{device.key}_{suffix}"

    @property
    def xiaodu_device(self) -> XiaoduDevice | None:
        return self.coordinator.get_device_by_key(self._device_key)

    @property
    def device_info(self) -> DeviceInfo:
        device = self.xiaodu_device
        name = device.name if device else self._device_key
        model = device.device_name if device else "Xiaodu device"
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_key)},
            name=name,
            manufacturer="Baidu Xiaodu",
            model=model,
        )

    @property
    def available(self) -> bool:
        device = self.xiaodu_device
        return super().available and device is not None and device.online is not False
