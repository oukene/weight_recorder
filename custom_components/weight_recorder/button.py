import logging
from homeassistant.const import (
    STATE_UNKNOWN, STATE_UNAVAILABLE, ATTR_UNIT_OF_MEASUREMENT
)

from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.components.button import ButtonEntity
from .hub import *

from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)


_LOGGER = logging.getLogger(__name__)

ENTITY_ID_FORMAT = DOMAIN + ".{}"


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
        s = WeightRecorderButton(hass, entry.entry_id, device, "unrecorded input")
        new_devices.append(s)
        s = WeightRecorderButton(hass, entry.entry_id, device, "unrecorded remove")
        new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderButton(EntityBase, ButtonEntity):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry_id, device, type):
        """Initialize the sensor."""
        super().__init__(device)
        self.entry_id = entry_id
        self.hass = hass
        _LOGGER.debug("configure : " + str(device.configure))

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, type), hass=hass)
        _LOGGER.debug("entity id : " + str(self.entity_id))
        self._name = "{}".format(type)
        self._attributes = {}
        self._unique_id = self.entity_id
        self._device = device
        self._type = type

        self._hub = hass.data[DOMAIN][entry_id]["hub"]

    # def unique_id(self):
    #    """Return Unique ID string."""
    #    return self.unique_id

    async def async_press(self) -> None:
        """Change the selected option."""
        if self._type == "unrecorded input":
            key = self._device.unrecorded_entity.current_option.split(" - ")[0]
            value = self._device.unrecorded_entity.current_option.split(" - ")[1]
            await self._device.weight_entity.async_set_value(float(value))

        await self._device.unrecorded_entity.async_remove_option(key)


