from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig
import voluptuous as vol

from .client import XiaoduDevice, XiaoduMcpClient
from .const import CONF_BASE_URL, DATA_CLIENT, DATA_COORDINATOR, DATA_PHOTOS, DOMAIN, PLATFORMS
from .coordinator import XiaoduCoordinator

_LOGGER = logging.getLogger(__name__)

type XiaoduConfigEntry = ConfigEntry


def _entry_data(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    return hass.data[DOMAIN][entry.entry_id]


def _resolve_device_from_call(hass: HomeAssistant, coordinator: XiaoduCoordinator, call: ServiceCall) -> XiaoduDevice:
    data = call.data
    # Prefer explicit key/name.
    if key := data.get("device_key"):
        device = coordinator.get_device_by_key(str(key))
        if device:
            return device
    if name := data.get("device"):
        device = coordinator.get_device_by_name(str(name))
        if device:
            return device

    # Resolve from target entity/device if supplied by HA service target.
    entity_ids = data.get("entity_id") or []
    if isinstance(entity_ids, str):
        entity_ids = [entity_ids]
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    for entity_id in entity_ids:
        entry = ent_reg.async_get(entity_id)
        if entry and entry.unique_id:
            # unique ids use f"{device.key}_..."
            for device in coordinator.data or []:
                if entry.unique_id.startswith(device.key):
                    return device

    device_ids = data.get("device_id") or []
    if isinstance(device_ids, str):
        device_ids = [device_ids]
    for device_id in device_ids:
        dev_entry = dev_reg.async_get(device_id)
        if not dev_entry:
            continue
        for identifier in dev_entry.identifiers:
            if identifier[0] == DOMAIN:
                device = coordinator.get_device_by_key(identifier[1])
                if device:
                    return device

    if coordinator.data:
        raise vol.Invalid("Specify device_key, device name, entity_id, or device_id for Xiaodu MCP service")
    raise vol.Invalid("No Xiaodu devices available. Call xiaodu_mcp.refresh_devices or check token-proxy /api/devices")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    session = async_get_clientsession(hass)
    client = XiaoduMcpClient(session, entry.data[CONF_BASE_URL])
    coordinator = XiaoduCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
        DATA_PHOTOS: {},
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_refresh_devices(call: ServiceCall) -> None:
        await coordinator.async_request_refresh()

    async def handle_speak(call: ServiceCall) -> None:
        device = _resolve_device_from_call(hass, coordinator, call)
        await client.speak(device, str(call.data["text"]))

    async def handle_command(call: ServiceCall) -> None:
        device = _resolve_device_from_call(hass, coordinator, call)
        await client.command(device, str(call.data["command"]))

    async def handle_take_photo(call: ServiceCall) -> None:
        device = _resolve_device_from_call(hass, coordinator, call)
        image = await client.take_photo(device)
        if image:
            _entry_data(hass, entry)[DATA_PHOTOS][device.key] = image
        await coordinator.async_request_refresh()

    # Register once per domain; handlers use the first loaded entry for simplicity in MVP.
    if not hass.services.has_service(DOMAIN, "refresh_devices"):
        hass.services.async_register(DOMAIN, "refresh_devices", handle_refresh_devices)
        hass.services.async_register(
            DOMAIN,
            "speak",
            handle_speak,
            schema=vol.Schema({vol.Required("text"): str, vol.Optional("device"): str, vol.Optional("device_key"): str, vol.Optional("entity_id"): vol.Any(str, [str]), vol.Optional("device_id"): vol.Any(str, [str])}),
            supports_response=False,
        )
        hass.services.async_register(
            DOMAIN,
            "command",
            handle_command,
            schema=vol.Schema({vol.Required("command"): str, vol.Optional("device"): str, vol.Optional("device_key"): str, vol.Optional("entity_id"): vol.Any(str, [str]), vol.Optional("device_id"): vol.Any(str, [str])}),
            supports_response=False,
        )
        hass.services.async_register(
            DOMAIN,
            "take_photo",
            handle_take_photo,
            schema=vol.Schema({vol.Optional("device"): str, vol.Optional("device_key"): str, vol.Optional("entity_id"): vol.Any(str, [str]), vol.Optional("device_id"): vol.Any(str, [str])}),
            supports_response=False,
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
