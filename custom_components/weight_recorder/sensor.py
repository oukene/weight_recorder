import logging
from homeassistant.const import (
    STATE_UNKNOWN, STATE_UNAVAILABLE, ATTR_UNIT_OF_MEASUREMENT
)

from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change
from homeassistant.components.sensor import RestoreSensor
from .hub import *
from .hub import _is_valid_state, _in_range

from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)


_LOGGER = logging.getLogger(__name__)

ENTITY_ID_FORMAT = DOMAIN + ".{}"


async def async_setup_entry(hass, entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""
        
    new_devices = []
    hub = hass.data[DOMAIN][entry.entry_id]["hub"]
    devices = hub.devices
    _LOGGER.debug("devices : " +str(devices))
    weight_entity_id = entry.options.get(CONF_WEIGHT_ENTITY)

    for device_id, device in devices.items():
        _LOGGER.debug("find device id : " + str(device.device_id))
        _LOGGER.debug("conf : " + str(device.configure))
        s = WeightRecorderSensor(hass, entry.entry_id,device, weight_entity_id)
        new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderSensor(EntityBase, RestoreSensor):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry_id, device, weight_entity_id):
        """Initialize the sensor."""
        super().__init__(device)
        self.entry_id = entry_id
        self.hass = hass
        _LOGGER.debug("configure : " + str(device.configure))
        entity_name= device.configure.get(CONF_NAME)
        self._source_entity = weight_entity_id
        self._admit_range = device.configure.get(CONF_ADMIT_RANGE)

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, CONF_DEFAULT_ENTITY_NAME), hass=hass)
        _LOGGER.debug("entity id : " + str(self.entity_id))
        self._name = "{}".format(CONF_DEFAULT_ENTITY_NAME)
        self._value = None
        self._attributes = {}
        self._attributes[CONF_HEIGHT] = device.configure.get(CONF_HEIGHT)
        self._unit_of_measurement = CONF_DEFAULT_UNIT
        self._unique_id = self.entity_id
        self._device = device

        if device_id := device.configure.get("device_id"):
            modify_device_name = device.configure.get(CONF_NAME)

            device_registry = dr.async_get(self.hass)
            entity_registry = er.async_get(self.hass)
            _LOGGER.debug("set modify name device_id : " +str(device_id) + ", name : " + str(modify_device_name))
            device_registry.async_update_device(device_id, name_by_user=modify_device_name)

        self._hub = hass.data[DOMAIN][entry_id]["hub"]
        self._device.weight_entity = self

        self.setup()

    def setup(self):
        """"""
        # self.hass.data[DOMAIN][self.entry_id]["listener"].append(async_track_state_change(self.hass, self._source_entity, self.entity_listener))

        # state = self.hass.states.get(self._source_entity)
        # _LOGGER.debug("entity id : %s", self.entity_id)
        # old_state = self.hass.states.get(self.entity_id)
        # if _is_valid_state(state):
        #     self.entity_listener(self._source_entity, old_state, state)

    async def calc_attribute(self):
        # BMI calc
        if isNumber(self._value):
            height = self._attributes.get(CONF_HEIGHT) / 100
            _LOGGER.debug("calc BMI - weight : " + str(self._value) + ", height : " + str(height))
            self._attributes[CONF_BMI] = float(self._value) / (float(height) * float(height))


    async def async_added_to_hass(self):
        value = self._device.configure.get(CONF_WEIGHT)
        _LOGGER.debug("async_added_to_hass - conf value : " + str(value))
        old_state = await self.async_get_last_sensor_data()
        if old_state != None and old_state.native_value != None:
            value = old_state.native_value

        await self.async_set_value(value)
        #self._unit_of_measurement = old_state.native_unit_of_measurement
        
        self._device.register_callback(self.async_write_ha_state)

    def check_range(self, value: float) -> bool:
        return _in_range(float(value), float(self._value) - float(self._admit_range), float(self._value) + float(self._admit_range))

    async def async_set_value(self, value):
        self._value = value
        _LOGGER.debug("set native value : " + str(value))
        await self.calc_attribute()

        self.async_schedule_update_ha_state(True)

    # async def entity_listener(self, entity, old_state, new_state):
    #     if _is_valid_state(new_state):
    #         self._unit_of_measurement = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) if new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) else "kg"
    #         _LOGGER.debug("old state : " + str(old_state))
    #         _LOGGER.debug("new state : " + str(new_state))
    #         if old_state != None and new_state != None and old_state.state != new_state.state:
    #             value = new_state.state * 0.453592 if self._unit_of_measurement == "lbs" else new_state.state
    #             if _in_range(float(value), float(self._value) - float(self._admit_range), float(self._value) + float(self._admit_range)):
    #                 await self.async_set_value(value)
    #             else:
    #                 # unrecorded data process
    #                 self._hub.add_unrecorded_data(value)


    # def unique_id(self):
    #    """Return Unique ID string."""
    #    return self.unique_id

    @property
    def native_value(self):
        return self._value

    @property
    def state(self):
        """Return the state of the sensor."""
        # return self._state
        return self._value

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit_of_measurement


