import asyncio

from .const import *
from homeassistant.helpers.entity import Entity
import logging
from homeassistant.helpers.event import async_track_state_change
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE

def isNumber(s):
    try:
        if s != None:
            float(s)
            return True
        else:
            return False
    except ValueError:
        return False


def _is_valid_state(state) -> bool:
    return state and state.state != STATE_UNKNOWN and state.state != STATE_UNAVAILABLE


def _in_range(n, start, end=0):
    return start <= n <= end if end >= start else end <= n <= start

_LOGGER = logging.getLogger(__name__)

class EntityBase(Entity):
    """Base representation of a Hello World Sensor."""

    should_poll = False

    def __init__(self, device):
        """Initialize the sensor."""
        self._device = device

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._device.device_id)},
            "name": self._device.name,
            "sw_version": self._device.firmware_version,
            "model": self._device.model,
            "manufacturer": self._device.manufacturer
        }

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    async def async_added_to_hass(self):
        self._device.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        self._device.remove_callback(self.async_write_ha_state)

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._unique_id is not None:
            return self._unique_id

    @property
    def has_entity_name(self) -> bool:
        return True

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes

class Device:
    def __init__(self, name, config, conf):
        self._id = f"{name}_{config.entry_id}"
        self._name = name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._conf = conf.get(CONF_MODIFY_CONF) if conf.get(CONF_MODIFY_CONF) else conf
        self.firmware_version = VERSION
        self.model = NAME
        self.manufacturer = MANUFACTURE
        self.__weight_entity = None
        self.__unrecorded_entity = None

    @property
    def device_id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def configure(self):
        return self._conf

    def register_callback(self, callback):
        """Register callback, called when Roller changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    def publish_updates(self):
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    @property
    def weight_entity(self):
        return self.__weight_entity

    @weight_entity.setter
    def weight_entity(self, entity):
        self.__weight_entity = entity

    @property
    def unrecorded_entity(self):
        return self.__unrecorded_entity

    @unrecorded_entity.setter
    def unrecorded_entity(self, entity):
        self.__unrecorded_entity = entity


class Hub:
    def __init__(self, hass, entry, weight_entity_id) -> None:
        self.__devices = {}
        self.hass = hass
        self.entry = entry
        self._weight_entity_id = weight_entity_id
        self.setup()

    def setup(self):
        self.hass.data[DOMAIN][self.entry.entry_id]["listener"].append(
            async_track_state_change(self.hass, self._weight_entity_id, self.entity_listener))

    async def entity_listener(self, entity, old_state, new_state):
        _LOGGER.debug("call entity_listener")
        in_range_count = 0
        submit_entity = None
        for device_id, device in self.devices.items():
            _LOGGER.debug("new_state : " + str(new_state))
            if device and device.weight_entity:
                if device.weight_entity.check_range(new_state.state):
                    in_range_count += 1
                    submit_entity = device.weight_entity
        
        if in_range_count == 1:
            await submit_entity.async_set_value(new_state.state)
        else:
            """"""
            # unrecorded data process
            for device_id, device in self.devices.items():
                if device and device.unrecorded_entity:
                    await device.unrecorded_entity.async_add_option(new_state.state)

        # if _is_valid_state(new_state):
        #     self._unit_of_measurement = new_state.attributes.get(
        #         ATTR_UNIT_OF_MEASUREMENT) if new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) else "kg"
        #     _LOGGER.debug("old state : " + str(old_state))
        #     _LOGGER.debug("new state : " + str(new_state))
        #     if old_state != None and new_state != None and old_state.state != new_state.state:
        #         value = new_state.state * \
        #             0.453592 if self._unit_of_measurement == "lbs" else new_state.state
        #         if _in_range(float(value), float(self._value) - float(self._admit_range), float(self._value) + float(self._admit_range)):
        #             await self.async_set_value(value)
        #         else:
        #             # unrecorded data process
        #             self._hub.add_unrecorded_data(value)


    def add_device(self, device:Device) -> None:
        self.__devices[device.device_id] = device

    @property
    def device(self, device_id:str) -> Device:
        return self.__devices.get(device_id, None)

    @property
    def devices(self) -> dict[str, Device]:
        return self.__devices

    @devices.setter
    def devices(self, devices):
        self.__devices = devices



