"""The Versatile Thermostat integration."""
from __future__ import annotations

from typing import Dict

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .climate import VersatileThermostat

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Versatile Thermostat from a config entry."""

    _LOGGER.debug(
        "Calling async_setup_entry entry: entry_id='%s', value='%s'",
        entry.entry_id,
        entry.data,
    )

    # hass.data.setdefault(DOMAIN, {})

    # TODO 1. Create API instance
    api: VersatileThermostatAPI = hass.data.get(DOMAIN)
    if api is None:
        api = VersatileThermostatAPI(hass)

    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    api.add_entry(entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    api: VersatileThermostatAPI = hass.data.get(DOMAIN)

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        if api:
            api.remove_entry(entry)

    return unload_ok


class VersatileThermostatAPI(Dict):
    """The VersatileThermostatAPI"""

    _hass: HomeAssistant
    # _entries: Dict(str, ConfigEntry)

    def __init__(self, hass):
        _LOGGER.debug("building a VersatileThermostatAPI")
        super().__init__()
        self._hass = hass
        # self._entries = dict()
        # Add the API in hass.data
        self._hass.data[DOMAIN] = self

    def add_entry(self, entry: ConfigEntry):
        """Add a new entry"""
        _LOGGER.debug("Add the entry %s", entry.entry_id)
        # self._entries[entry.entry_id] = entry
        # Add the entry in hass.data
        self._hass.data[DOMAIN][entry.entry_id] = entry

    def remove_entry(self, entry: ConfigEntry):
        """Remove an entry"""
        _LOGGER.debug("Remove the entry %s", entry.entry_id)
        # self._entries.pop(entry.entry_id)
        self._hass.data[DOMAIN].pop(entry.entry_id)
        # If not more entries are preset, remove the API
        if len(self) == 0:
            _LOGGER.debug("No more entries-> Remove the API from DOMAIN")
            self._hass.data.pop(DOMAIN)

    @property
    def hass(self):
        """Get the HomeAssistant object"""
        return self._hass