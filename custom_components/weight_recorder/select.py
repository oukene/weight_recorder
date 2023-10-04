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

    for device_id, device in devices.items():
        _LOGGER.debug("find device id : " + str(device.device_id))
        _LOGGER.debug("conf : " + str(device.configure))
        s = WeightRecorderSelect(hass, entry, device)
        new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderSelect(EntityBase, SelectEntity):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry, device):
        """Initialize the sensor."""
        super().__init__(device)
        self.entry = entry
        self.hass = hass
        _LOGGER.debug("configure : " + str(device.configure))

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, "unrecorded data"), hass=hass)
        _LOGGER.debug("entity id : " + str(self.entity_id))
        self._name = "{}".format("unrecorded data")
        self._attributes = {}
        self._unique_id = entry.entry_id + "." + self._device.name + "." + "unrecorded_data"
        self._device = device
        self._options = []
        for key, value in entry.options.get("unrecorded_data").items():
            _LOGGER.debug("key : " + str(key))
            date_time_obj = datetime.strptime(key, "%Y-%m-%d %H:%M:%S")
            self._options.append(date_time_obj.strftime('%Y-%m-%d %H:%M:%S') + " - " + value)

        #self._options = list(entry.options.get("unrecorded_data").values())
        self._current_option = self._options[0] if len(self._options) > 0 else None

        self._hub = hass.data[DOMAIN][entry.entry_id]["hub"]
        self._device.unrecorded_entity = self

    # def unique_id(self):
    #    """Return Unique ID string."""
    #    return self.unique_id

    async def async_add_option(self, option):        
        entry_options = self.entry.options        
        entry_options["unrecorded_data"][datetime.now().strftime('%Y-%m-%d %H:%M:%S')] = (str(option))
        _LOGGER.debug("entry_options : " + str(entry_options))

        self.hass.config_entries.async_update_entry(
            self.entry,
            options={
                CONF_WEIGHT_ENTITY: entry_options.get(CONF_WEIGHT_ENTITY),
                CONF_ENTITIES: entry_options.get(CONF_ENTITIES),
                "unrecorded_data": entry_options.get("unrecorded_data"),
                "modifydatetime": datetime.now(),
            }
        )

    async def async_remove_option(self, option):
        entry_options = self.entry.options
        del entry_options["unrecorded_data"][option]
        _LOGGER.debug("entry_options : " + str(entry_options))

        self.hass.config_entries.async_update_entry(
            self.entry,
            options={
                CONF_WEIGHT_ENTITY: entry_options.get(CONF_WEIGHT_ENTITY),
                CONF_ENTITIES: entry_options.get(CONF_ENTITIES),
                "unrecorded_data": entry_options.get("unrecorded_data"),
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

