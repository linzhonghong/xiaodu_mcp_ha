from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DATA_PHOTOS, DOMAIN
from .entity import XiaoduEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]
    photos = data[DATA_PHOTOS]
    async_add_entities([XiaoduCamera(coordinator, photos, device) for device in coordinator.data or []])


class XiaoduCamera(XiaoduEntity, Camera):
    _attr_name = "最近拍照"
    _attr_supported_features = 0

    def __init__(self, coordinator, photos, device) -> None:
        Camera.__init__(self)
        XiaoduEntity.__init__(self, coordinator, device, "latest_photo")
        self._photos = photos

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        return self._photos.get(self._device_key)
