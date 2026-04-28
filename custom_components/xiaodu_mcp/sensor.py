from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .entity import XiaoduEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([XiaoduStatusSensor(coordinator, device) for device in coordinator.data or []])


class XiaoduStatusSensor(XiaoduEntity, SensorEntity):
    _attr_name = "状态"

    def __init__(self, coordinator, device) -> None:
        super().__init__(coordinator, device, "status")

    @property
    def native_value(self):
        device = self.xiaodu_device
        if not device:
            return "unknown"
        return "online" if device.online else "offline"

    @property
    def extra_state_attributes(self):
        device = self.xiaodu_device
        if not device:
            return {}
        return {
            "device_name": device.device_name,
            "client_id": device.client_id,
            "cuid": device.cuid,
            "house": device.house,
            "floor": device.floor,
            "room": device.room,
        }
