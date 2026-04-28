from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_CLIENT, DATA_COORDINATOR, DATA_PHOTOS, DOMAIN
from .entity import XiaoduEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]
    client = data[DATA_CLIENT]
    photos = data[DATA_PHOTOS]
    entities = []
    for device in coordinator.data or []:
        entities.append(XiaoduTestSpeakButton(coordinator, client, device))
        entities.append(XiaoduTakePhotoButton(coordinator, client, photos, device))
    async_add_entities(entities)


class XiaoduTestSpeakButton(XiaoduEntity, ButtonEntity):
    _attr_name = "测试播报"

    def __init__(self, coordinator, client, device) -> None:
        super().__init__(coordinator, device, "test_speak")
        self._client = client

    async def async_press(self) -> None:
        device = self.xiaodu_device
        if device:
            await self._client.speak(device, "这是一条来自 Home Assistant 的测试播报")


class XiaoduTakePhotoButton(XiaoduEntity, ButtonEntity):
    _attr_name = "拍照"

    def __init__(self, coordinator, client, photos, device) -> None:
        super().__init__(coordinator, device, "take_photo")
        self._client = client
        self._photos = photos

    async def async_press(self) -> None:
        device = self.xiaodu_device
        if device:
            image = await self._client.take_photo(device)
            if image:
                self._photos[device.key] = image
