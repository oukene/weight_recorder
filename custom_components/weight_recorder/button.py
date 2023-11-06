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

    for device_id, device in devices.items():
        if entry.options.get(CONF_USE_UNRECORDED_DATA):
            if device.isHub():
                s = WeightRecorderButton(hass, entry.entry_id, device, TRANS_KEY_UNRECORDED_INPUT)
                new_devices.append(s)
                s = WeightRecorderButton(hass, entry.entry_id, device, TRANS_KEY_UNRECORDED_REMOVE)
                new_devices.append(s)
                s = WeightRecorderButton(hass, entry.entry_id, device, TRANS_KEY_UNRECORDED_CLEAR)
                new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderButton(EntityBase, ButtonEntity):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry_id, device, translation_key):
        """Initialize the sensor."""
        EntityBase.__init__(self, device, translation_key=translation_key)
        self.entry_id = entry_id
        self.hass = hass

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, translation_key), hass=hass)
        self._name = "{}".format(translation_key)
        self._attributes = {}
        self._unique_id = self.entity_id
        self._device = device
        self._translation_key = translation_key

        self._hub = hass.data[DOMAIN][entry_id]["hub"]

    # def unique_id(self):
    #    """Return Unique ID string."""
    #    return self.unique_id

    async def async_press(self) -> None:
        """Change the selected option."""
        hub = self.hass.data[DOMAIN][self.entry_id]["hub"]
        if self._translation_key == TRANS_KEY_UNRECORDED_INPUT:
            await hub.record_data()
        elif self._translation_key == TRANS_KEY_UNRECORDED_REMOVE:
            await hub.remove_data()
        elif self._translation_key == TRANS_KEY_UNRECORDED_CLEAR:
            await hub.clear_data()
            #await self._device.weight_entity.async_set_value(float(value))

        #await self._device.unrecorded_entity.async_remove_option(time)


