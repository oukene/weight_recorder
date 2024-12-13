import logging
from homeassistant.const import (
    STATE_UNKNOWN, STATE_UNAVAILABLE, ATTR_UNIT_OF_MEASUREMENT
)

from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.components.number import NumberEntity, NumberMode
from .hub import *

from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)

from operator import eq

_LOGGER = logging.getLogger(__name__)

ENTITY_ID_FORMAT = "number" + ".{}"


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
        if not device.isHub() and device.configure.get(CONF_USE_MANUAL_INPUT, False):
            s = WeightRecorderNumber(hass, entry.entry_id, device, "kg", translation_key=TRANS_KEY_MANUAL_INPUT_WEIGHT)
            new_devices.append(s)
            s = WeightRecorderNumber(hass, entry.entry_id, device, "cm", translation_key=TRANS_KEY_MANUAL_INPUT_HEIGHT)
            new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderNumber(EntityBase, NumberEntity):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry_id, device, unit, translation_key):
        """Initialize the sensor."""
        super().__init__(device, translation_key=translation_key)
        self.entry_id = entry_id
        self.hass = hass

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, translation_key), current_ids="", hass=hass)
        self._name = "{}".format(translation_key)
        self._unit_of_measurement = unit
        self._value = 0
        self._attributes = {}
        self._unique_id = self.entity_id
        self._device = device

        self._hub = hass.data[DOMAIN][entry_id]["hub"]

    # def unique_id(self):
    #    """Return Unique ID string."""
    #    return self.unique_id

    @property
    def mode(self) -> NumberMode:
        return NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        return self._value

    @property
    def native_max_value(self) -> float:
        return 10000

    @property
    def native_min_value(self) -> float:
        return 0

    @property
    def native_step(self) -> float | None:
        return 0.1

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit_of_measurement

    async def async_set_native_value(self, value: float) -> None:
        if eq(self._translation_key, TRANS_KEY_MANUAL_INPUT_WEIGHT):
            await self._device.get_sensor(SENSOR_KEY.WEIGHT.value).async_set_value(value)
        elif eq(self._translation_key, TRANS_KEY_MANUAL_INPUT_HEIGHT):
            await self._device.get_sensor(SENSOR_KEY.HEIGHT.value).async_set_value(value)

        self._value = value
        await self.async_update_ha_state()
