"""The Detailed Hello World Push integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import *
from .hub import Hub, Device

from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)
import re

_LOGGER = logging.getLogger(__name__)

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS_1 = ["sensor", "number", "button"]
PLATFORMS_2 = ["select"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Hello World component."""
    # Ensure our name space for storing objects is a known type. A dict is
    # common/preferred as it allows a separate instance of your class for each
    # instance that has been created in the UI.
    _LOGGER.debug("call async_setup")
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hello World from a config entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    _LOGGER.debug("call async_setup_entry")
    #hass.data[DOMAIN][entry.entry_id] = DOMAIN
    #hass.data[DOMAIN][entry.entry_id] = {}
    hass_loading = hass.data[DOMAIN].get(entry.entry_id, {}).get("hass_loading", True)
    hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id]["hass_loading"] = hass_loading

    hass.data[DOMAIN][entry.entry_id]["listener"] = []

    entry.async_on_unload(entry.add_update_listener(update_listener))

    # hide / unhide
    # devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)

    # for d in devices:
    #     if entry.options.get(CONF_USE_UNRECORDED_DATA):
    #         if re.search("Hub", d.name):
    #             dr.async_get(hass).async_update_device(
    #                 d.id, disabled_by=None)
    #     else:
    #         if re.search("Hub", d.name):
    #             dr.async_get(hass).async_update_device(
    #                 d.id, disabled_by=dr.DeviceEntryDisabler.USER)

    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    
    for e in entities:
        _LOGGER.debug("device_id : " + str(e.device_id) + ", device_name : " +
                      str(dr.async_get(hass).async_get(e.device_id).name))
        if entry.options.get(CONF_USE_UNRECORDED_DATA):
            if re.search("_Hub", str(dr.async_get(hass).async_get(e.device_id).name)):
                er.async_get(hass).async_update_entity(e.entity_id, hidden_by=None)
        else:
            if re.search("_Hub", str(dr.async_get(hass).async_get(e.device_id).name)) and e.translation_key != TRANS_KEY_WEIGHT:
                er.async_get(hass).async_update_entity(e.entity_id, hidden_by=er.RegistryEntryHider.USER)

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    if weight_entity_id := entry.options.get(CONF_WEIGHT_ENTITY, None):
        hub = Hub(hass, entry, weight_entity_id)
        hass.data[DOMAIN][entry.entry_id]["hub"] = hub

        device = Device(hass, entry.data.get(CONF_NAME) + "_Hub", entry, {}, DeviceType.HUB)
        hub.add_device(device)
        for key, conf in entry.options.get(CONF_ENTITIES, {}).items():
            device = Device(hass, conf.get(CONF_NAME), entry, conf, DeviceType.PROFILE)
            hub.add_device(device)

        #device = Device(entry.data[CONF_NAME]+"manager", entry, {})

        all(
            await asyncio.gather(
                *[
                    hass.async_create_task(
                        hass.config_entries.async_forward_entry_setup(entry, component))
                    for component in PLATFORMS_1
                ]
            )
        )

        for component in PLATFORMS_2:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, component)
            )

    return True


async def update_listener(hass, entry):
    """Handle options update."""
    _LOGGER.debug("call update_listener")
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    _LOGGER.debug("call async_unload_entry")

    for listener in hass.data[DOMAIN][entry.entry_id]["listener"]:
        listener()
    unload_ok = True
    if hass.data[DOMAIN][entry.entry_id].get("hub"):
        unload_ok = all(
            await asyncio.gather(
                *[
                    hass.config_entries.async_forward_entry_unload(
                        entry, component)
                    for component in PLATFORMS_1 + PLATFORMS_2
                ]
            )
        )

    #if unload_ok:
    #    hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
