import logging
from homeassistant.const import (
    STATE_UNKNOWN, STATE_UNAVAILABLE, ATTR_UNIT_OF_MEASUREMENT
)

from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change
from homeassistant.components.number import NumberEntity, NumberMode
from .hub import *

from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)


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
            s = WeightRecorderNumber(hass, entry.entry_id, device, translation_key=TRANS_KEY_MANUAL_INPUT)
            new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderNumber(EntityBase, NumberEntity):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry_id, device, translation_key):
        """Initialize the sensor."""
        super().__init__(device, translation_key=translation_key)
        self.entry_id = entry_id
        self.hass = hass

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, "manual input"), current_ids="", hass=hass)
        self._name = "{}".format("manual input")
        self._unit_of_measurement = "kg"
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
        await self._device.get_sensor(SENSOR_KEY.WEIGHT).async_set_value(value, self._unit_of_measurement)
        self._value = None