from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN
from .entity import XiaoduEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]
    client = data[DATA_CLIENT]
    entities = []
    for device in coordinator.data or []:
        entities.append(XiaoduSpeakText(coordinator, client, device))
        entities.append(XiaoduCommandText(coordinator, client, device))
    async_add_entities(entities)


class XiaoduSpeakText(XiaoduEntity, TextEntity):
    _attr_name = "播报文本"
    _attr_native_min = 0
    _attr_native_max = 500

    def __init__(self, coordinator, client, device) -> None:
        super().__init__(coordinator, device, "speak_text")
        self._client = client
        self._value = ""

    @property
    def native_value(self) -> str:
        return self._value

    async def async_set_value(self, value: str) -> None:
        self._value = value
        device = self.xiaodu_device
        if device and value:
            await self._client.speak(device, value)
        self.async_write_ha_state()


class XiaoduCommandText(XiaoduEntity, TextEntity):
    _attr_name = "自然语言指令"
    _attr_native_min = 0
    _attr_native_max = 500

    def __init__(self, coordinator, client, device) -> None:
        super().__init__(coordinator, device, "command_text")
        self._client = client
        self._value = ""

    @property
    def native_value(self) -> str:
        return self._value

    async def async_set_value(self, value: str) -> None:
        self._value = value
        device = self.xiaodu_device
        if device and value:
            await self._client.command(device, value)
        self.async_write_ha_state()
