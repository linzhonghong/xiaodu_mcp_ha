from __future__ import annotations

import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class XiaoduDevice:
    key: str
    name: str
    device_name: str
    client_id: str
    cuid: str
    online: bool | None = None
    house: str | None = None
    floor: str | None = None
    room: str | None = None
    raw: dict[str, Any] | None = None


class XiaoduMcpClientError(Exception):
    """Raised when xiaodu-token-proxy returns an error."""


class XiaoduMcpClient:
    """Client for xiaodu-token-proxy v2 /api endpoints."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")

    async def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        timeout = aiohttp.ClientTimeout(total=120)
        try:
            async with self._session.request(method, url, timeout=timeout, **kwargs) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    raise XiaoduMcpClientError(f"{method} {url} failed: {resp.status} {text}")
                if not text:
                    return {}
                try:
                    return json.loads(text)
                except json.JSONDecodeError as err:
                    raise XiaoduMcpClientError(f"Invalid JSON from {url}: {text[:500]}") from err
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise XiaoduMcpClientError(f"Failed to call {url}: {err}") from err

    async def health(self) -> dict[str, Any]:
        return await self._request_json("GET", "/health")

    async def devices(self) -> list[XiaoduDevice]:
        payload = await self._request_json("GET", "/api/devices")
        raw_devices = payload.get("devices", payload if isinstance(payload, list) else [])
        devices: list[XiaoduDevice] = []
        if not isinstance(raw_devices, list):
            raise XiaoduMcpClientError(f"Unexpected /api/devices payload: {payload}")
        for item in raw_devices:
            if not isinstance(item, dict):
                continue
            cuid = str(item.get("cuid") or "")
            client_id = str(item.get("client_id") or "")
            if not cuid or not client_id:
                _LOGGER.warning("Skipping Xiaodu device without cuid/client_id: %s", item)
                continue
            device_name = str(item.get("device_name") or item.get("name") or "小度设备")
            location = item.get("location") if isinstance(item.get("location"), dict) else {}
            room = item.get("room") or location.get("room")
            house = item.get("house") or location.get("house")
            floor = item.get("floor") or location.get("floor")
            name = str(item.get("name") or f"{room or ''} {device_name}".strip() or device_name)
            key = str(item.get("key") or cuid)
            online = item.get("online")
            if online is None:
                online = item.get("online_status")
            devices.append(
                XiaoduDevice(
                    key=key,
                    name=name,
                    device_name=device_name,
                    client_id=client_id,
                    cuid=cuid,
                    online=bool(online) if online is not None else None,
                    house=house,
                    floor=floor,
                    room=room,
                    raw=item,
                )
            )
        return devices

    async def speak(self, device: XiaoduDevice, text: str) -> dict[str, Any]:
        return await self._request_json(
            "POST",
            "/api/speak",
            json={"client_id": device.client_id, "cuid": device.cuid, "text": text},
        )

    async def command(self, device: XiaoduDevice, command: str) -> dict[str, Any]:
        return await self._request_json(
            "POST",
            "/api/command",
            json={"client_id": device.client_id, "cuid": device.cuid, "command": command},
        )

    async def take_photo(self, device: XiaoduDevice) -> bytes | None:
        payload = await self._request_json(
            "POST",
            "/api/take_photo",
            json={"client_id": device.client_id, "cuid": device.cuid},
        )
        # token-proxy v2 may return image_base64, content, or nested MCP-style content.
        image_b64 = payload.get("image_base64") or payload.get("content") or payload.get("data")
        if not image_b64 and isinstance(payload.get("result"), dict):
            result = payload["result"]
            image_b64 = result.get("image_base64") or result.get("content") or result.get("data")
            for item in result.get("content", []) if isinstance(result.get("content"), list) else []:
                if isinstance(item, dict) and item.get("type") in {"image", "ImageContent"}:
                    image_b64 = item.get("data") or item.get("content")
                    break
        if not image_b64:
            return None
        if isinstance(image_b64, str) and image_b64.startswith("data:image"):
            image_b64 = image_b64.split(",", 1)[-1]
        try:
            return base64.b64decode(image_b64)
        except Exception as err:
            raise XiaoduMcpClientError("Failed to decode photo base64 from /api/take_photo") from err
