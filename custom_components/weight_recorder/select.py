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
import threading

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

    # device_registry = dr.async_get(hass)
    # devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    profile_list = {None:"-"}
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    # device_registry = dr.async_get(hass)
    # for d in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
    #     _LOGGER.debug("device info : " + str(d))
    #     if d.name != "Hub":
    #         profile_list[d.id] = d.name_by_user if d.name_by_user != None else d.name

    for e in entities:
        if e.translation_key == SENSOR_KEY.WEIGHT.value:
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
        if entry.options.get(CONF_USE_UNRECORDED_DATA):
            if device.isHub():
                s = WeightRecorderSelect(hass, entry, device, translation_key=TRANS_KEY_UNRECORDED_DATA, options={}, select_reset_time=-1)
                new_devices.append(s)

                s = WeightRecorderSelect(hass, entry, device, translation_key=TRANS_KEY_PROFILE_LIST, options=profile_list, select_reset_time=entry.options.get(CONF_SELECT_PROFILE_RESET_SECONDS, -1))
                new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderSelect(EntityBase, SelectEntity):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry, device, translation_key, options, select_reset_time):
        """Initialize the sensor."""
        super().__init__(device, translation_key=translation_key)
        self.entry = entry
        self.hass = hass

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, translation_key), current_ids="", hass=hass)
        #self._name = "{}".format("unrecorded data")
        self._attributes = {}
        self._unique_id = self.entity_id
        self._device = device
        self._profiles = options
        self._options = list(options.values())
        self._reset_time = select_reset_time

        hub = hass.data[DOMAIN][entry.entry_id]["hub"]

        if self._translation_key == TRANS_KEY_UNRECORDED_DATA:
            for key, value in entry.options.get(TRANS_KEY_UNRECORDED_DATA, {}).items():
                date_time_obj = datetime.strptime(key, "%Y-%m-%d %H:%M:%S")
                #self._options.append(date_time_obj.strftime('%Y-%m-%d %H:%M:%S') + "-" + value[0] + "-" + value[1])
                self._options.append(date_time_obj.strftime('%Y-%m-%d %H:%M:%S') + "-" + value[0] + "-" + value[1])
            
            hub.unrecorded_entity = self
        elif self._translation_key == TRANS_KEY_PROFILE_LIST:
            hub.profile_list_entity = self
            #self._options = list(entry.options.get("unrecorded_data").values())
        #self._current_option = self._options[0] if len(self._options) > 0 else None
        # if TRANS_KEY_PROFILE_LIST == self._translation_key:
        #     self._current_option = "None"
        # else:
        self._current_option = self._options[0] if len(self._options) > 0 else None

    # def unique_id(self):
    #    """Return Unique ID string."""
    #    return self.unique_id


    async def async_add_option(self, option, bia_value):        
        entry_options = self.entry.options
        # if not entry_options.get(TRANS_KEY_UNRECORDED_DATA):
        #     entry_options[TRANS_KEY_UNRECORDED_DATA] = {}

        entry_options[TRANS_KEY_UNRECORDED_DATA][datetime.now().strftime('%Y-%m-%d %H:%M:%S')] = ( (str(option)), bia_value )

        await self.update_entry(entry_options)


    async def update_entry(self, entry_options):
        _LOGGER.debug("update entry")
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={
                CONF_WEIGHT_DEVICES: entry_options.get(CONF_WEIGHT_DEVICES),
                CONF_PROFILES: entry_options.get(CONF_PROFILES),
                TRANS_KEY_UNRECORDED_DATA: entry_options.get(TRANS_KEY_UNRECORDED_DATA),
                CONF_USE_UNRECORDED_DATA: entry_options.get(CONF_USE_UNRECORDED_DATA),
                #CONF_SELECT_PROFILE_RESET_SECONDS: entry_options.get(CONF_SELECT_PROFILE_RESET_SECONDS),
                "modifydatetime": datetime.now(),
            }
        )

    async def async_remove_option(self, option):
        entry_options = self.entry.options
        del entry_options[TRANS_KEY_UNRECORDED_DATA][option]

        await self.update_entry(entry_options)

    async def async_clear_option(self):
        entry_options = self.entry.options
        _LOGGER.debug("entry_options : " + str(entry_options))
        entry_options[TRANS_KEY_UNRECORDED_DATA].clear()

        await self.update_entry(entry_options)

    @property
    def options(self) -> list[str]:
        return self._options

    @property
    def current_option(self) -> str | None:
        _LOGGER.debug("current option : " + str(self._current_option))
        return self._current_option

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug("async_select_option reset_time : " + str(self._reset_time))
        self._current_option = option

        # if self._reset_time > 0:
        #     try:
        #         self._loop.close()
        #     except:
        #         """"""
        #     self._loop = asyncio.new_event_loop()
        #     self._loop.run_until_complete(self.reset())
        #     self._loop.close()

    # async def reset(self):
    #     _LOGGER.debug("reset")
    #     await asyncio.sleep(self._reset_time)
    #     _LOGGER.debug("sleep end")
    #     await self.update_entry(self.entry.options)
    #     self._current_option = None

        
