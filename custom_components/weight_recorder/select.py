import logging
from copy import deepcopy

from homeassistant.components.select import SelectEntity, ENTITY_ID_FORMAT
from homeassistant.const import (ATTR_UNIT_OF_MEASUREMENT, STATE_UNAVAILABLE,
                                 STATE_UNKNOWN)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import async_generate_entity_id
from datetime import datetime
from .const import *
from .hub import *
import re

_LOGGER = logging.getLogger(__name__)

#ENTITY_ID_FORMAT = DOMAIN + ".{}"


def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_valid_state(state) -> bool:
    return state and state.state != STATE_UNKNOWN and state.state != STATE_UNAVAILABLE

async def async_setup_entry(hass, entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""

    new_devices = []
    hub = hass.data[DOMAIN][entry.entry_id]["hub"]
    devices = hub.devices
    _LOGGER.debug("devices : " + str(devices))

    # device_registry = dr.async_get(hass)
    # devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    profile_list = {}
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    # device_registry = dr.async_get(hass)
    # for d in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
    #     _LOGGER.debug("device info : " + str(d))
    #     if d.name != "Hub":
    #         profile_list[d.id] = d.name_by_user if d.name_by_user != None else d.name

    for e in entities:
        if e.translation_key == TRANS_KEY_WEIGHT:
            device = dr.async_get(hass).async_get(e.device_id)
            if not re.search("_Hub", device.name):
                profile_list[e.entity_id] = device.name_by_user if device.name_by_user != None else device.name

    # for e in entities:
    #     _LOGGER.debug("entity info : " + str(e))
    #     device_reg = dr.async_get(hass)
    #     device = device_reg.async_get(e.device_id)
    #     _LOGGER.debug("device info : " + str(device))
    #         device.name_by_user if device.name_by_user != None else device.name
    #profile_list = hub.weight_entities
    # for device_id, device in devices.items():
    #     if not device.isHub():
    #         _LOGGER.debug("find device : " + str(device))
    #         profile_list.append(device.name)


    for device_id, device in devices.items():
        _LOGGER.debug("device_id : " + str(device.device_id))
        if entry.options.get(CONF_USE_UNRECORDED_DATA):
            if device.isHub():
                s = WeightRecorderSelect(hass, entry, device, translation_key=TRANS_KEY_UNRECORDED_DATA, options={})
                new_devices.append(s)

                s = WeightRecorderSelect(hass, entry, device, translation_key=TRANS_KEY_PROFILE_LIST, options=profile_list)
                new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderSelect(EntityBase, SelectEntity):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry, device, translation_key, options):
        """Initialize the sensor."""
        super().__init__(device, translation_key=translation_key)
        self.entry = entry
        self.hass = hass
        _LOGGER.debug("configure : " + str(device.configure))

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, translation_key), hass=hass)
        _LOGGER.debug("entity id : " + str(self.entity_id))
        #self._name = "{}".format("unrecorded data")
        self._attributes = {}
        self._unique_id = entry.entry_id + "." + self._device.name + "." + translation_key
        self._device = device
        self._profiles = options
        self._options = list(options.values())

        hub = hass.data[DOMAIN][entry.entry_id]["hub"]

        if self._translation_key == TRANS_KEY_UNRECORDED_DATA:
            for key, value in entry.options.get(TRANS_KEY_UNRECORDED_DATA, {}).items():
                _LOGGER.debug("key : " + str(key))
                date_time_obj = datetime.strptime(key, "%Y-%m-%d %H:%M:%S")
                self._options.append(date_time_obj.strftime('%Y-%m-%d %H:%M:%S') + " - " + value)
            
            hub.unrecorded_entity = self
        elif self._translation_key == TRANS_KEY_PROFILE_LIST:
            hub.profile_list_entity = self
            #self._options = list(entry.options.get("unrecorded_data").values())
        self._current_option = self._options[0] if len(self._options) > 0 else None

    # def unique_id(self):
    #    """Return Unique ID string."""
    #    return self.unique_id

    async def async_add_option(self, option):        
        entry_options = self.entry.options
        # if not entry_options.get(TRANS_KEY_UNRECORDED_DATA):
        #     entry_options[TRANS_KEY_UNRECORDED_DATA] = {}

        entry_options[TRANS_KEY_UNRECORDED_DATA][datetime.now().strftime('%Y-%m-%d %H:%M:%S')] = (str(option))
        _LOGGER.debug("entry_options : " + str(entry_options))

        self.hass.config_entries.async_update_entry(
            self.entry,
            options={
                CONF_WEIGHT_ENTITY: entry_options.get(CONF_WEIGHT_ENTITY),
                CONF_ENTITIES: entry_options.get(CONF_ENTITIES),
                TRANS_KEY_UNRECORDED_DATA: entry_options.get(TRANS_KEY_UNRECORDED_DATA),
                CONF_USE_UNRECORDED_DATA: entry_options.get(CONF_USE_UNRECORDED_DATA),
                "modifydatetime": datetime.now(),
            }
        )

    async def async_remove_option(self, option):
        entry_options = self.entry.options
        del entry_options[TRANS_KEY_UNRECORDED_DATA][option]
        _LOGGER.debug("entry_options : " + str(entry_options))

        self.hass.config_entries.async_update_entry(
            self.entry,
            options={
                CONF_WEIGHT_ENTITY: entry_options.get(CONF_WEIGHT_ENTITY),
                CONF_ENTITIES: entry_options.get(CONF_ENTITIES),
                TRANS_KEY_UNRECORDED_DATA: entry_options.get(TRANS_KEY_UNRECORDED_DATA),
                CONF_USE_UNRECORDED_DATA: entry_options.get(CONF_USE_UNRECORDED_DATA),
                "modifydatetime": datetime.now(),
            }
        )
        # await self.hass.config_entries.async_unload(self.entry.entry_id)
        # await self.hass.config_entries.async_reload(self.entry.entry_id)

        #self.async_schedule_update_ha_state(True)

    @property
    def options(self) -> list[str]:
        return self._options

    @property
    def current_option(self) -> str | None:
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        self._current_option = option
        """Change the selected option."""

