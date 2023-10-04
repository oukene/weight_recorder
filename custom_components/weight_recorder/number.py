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
        s = WeightRecorderNumber(hass, entry.entry_id, device)
        new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderNumber(EntityBase, NumberEntity):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry_id, device):
        """Initialize the sensor."""
        super().__init__(device)
        self.entry_id = entry_id
        self.hass = hass
        _LOGGER.debug("configure : " + str(device.configure))

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, "manual input"), hass=hass)
        _LOGGER.debug("entity id : " + str(self.entity_id))
        self._name = "{}".format("manual input")
        self._unit_of_measurement = CONF_DEFAULT_UNIT
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
        await self._device.weight_entity.async_set_value(value)