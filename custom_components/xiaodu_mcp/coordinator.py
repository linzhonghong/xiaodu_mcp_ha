from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import XiaoduDevice, XiaoduMcpClient
from .const import DEFAULT_SCAN_INTERVAL_SECONDS, DOMAIN

_LOGGER = logging.getLogger(__name__)


class XiaoduCoordinator(DataUpdateCoordinator[list[XiaoduDevice]]):
    def __init__(self, hass: HomeAssistant, client: XiaoduMcpClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> list[XiaoduDevice]:
        return await self.client.devices()

    def get_device_by_key(self, key: str) -> XiaoduDevice | None:
        for device in self.data or []:
            if device.key == key or device.cuid == key:
                return device
        return None

    def get_device_by_name(self, name: str) -> XiaoduDevice | None:
        for device in self.data or []:
            if device.name == name or device.device_name == name:
                return device
        return None
