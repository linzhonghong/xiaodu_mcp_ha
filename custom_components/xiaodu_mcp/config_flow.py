from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import XiaoduMcpClient, XiaoduMcpClientError
from .const import CONF_BASE_URL, DOMAIN


async def _validate(hass: HomeAssistant, base_url: str) -> None:
    session = async_get_clientsession(hass)
    client = XiaoduMcpClient(session, base_url)
    await client.health()
    await client.devices()


class XiaoduMcpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            try:
                await _validate(self.hass, base_url)
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(base_url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Xiaodu MCP", data={CONF_BASE_URL: base_url})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_BASE_URL, default="http://127.0.0.1:8088"): str}),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return XiaoduMcpOptionsFlow(config_entry)


class XiaoduMcpOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({vol.Optional("note", default="Use xiaodu_mcp.refresh_devices to refresh device list."): str}),
            errors={},
        )
