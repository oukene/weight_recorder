import logging
from homeassistant.const import (
    STATE_UNKNOWN, STATE_UNAVAILABLE, ATTR_UNIT_OF_MEASUREMENT, DEVICE_CLASS_TIMESTAMP
)

from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change
from homeassistant.components.sensor import RestoreSensor, STATE_CLASS_MEASUREMENT, STATE_CLASS_TOTAL_INCREASING, SensorStateClass
from .hub import *
from .hub import _is_valid_state, _in_range

from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)

from datetime import datetime
import math


_LOGGER = logging.getLogger(__name__)

ENTITY_ID_FORMAT = "sensor" + ".{}"


def get_american_age(birthday, thatday):
    _LOGGER.debug("birthday : " + str(birthday) + ", thatday : " + str(thatday))
    this_year, today = int(thatday[:4]), thatday[4:]
    birth_year, birth_day = int(birthday[:4]), birthday[4:]
    my_age = this_year - birth_year

    if today < birth_day:
        my_age -= 1
    return my_age


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
        #if device.device_type == DeviceType.PROFILE:
        s = WeightRecorderSensor(hass, entry.entry_id, device, weight_entity_id, translation_key=TRANS_KEY_WEIGHT)
        new_devices.append(s)

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderSensor(EntityBase, RestoreSensor):
    """Representation of a Thermal Comfort Sensor."""

    def __init__(self, hass, entry_id, device, weight_entity_id, translation_key):
        """Initialize the sensor."""
        EntityBase.__init__(self, device, translation_key=translation_key)
        self.entry_id = entry_id
        self.hass = hass
        self._hub = hass.data[DOMAIN][entry_id]["hub"]

        _LOGGER.debug("configure : " + str(device.configure))
        entity_name= device.configure.get(CONF_NAME)
        self._source_entity = weight_entity_id
        self._admit_range = device.configure.get(CONF_ADMIT_RANGE)

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, CONF_DEFAULT_ENTITY_NAME), current_ids="", hass=hass)
        _LOGGER.debug("entity id : " + str(self.entity_id))
        self._name = "{}".format(CONF_DEFAULT_ENTITY_NAME)
        self._value = None
        self._attributes = {}
        if self._device.device_type == DeviceType.PROFILE:
            self._attributes[CONF_HEIGHT] = device.configure.get(CONF_HEIGHT)
            self._attributes[CONF_BIRTH] = device.configure.get(CONF_BIRTH)

        self._device.weight_entity = self

        self._unit_of_measurement = CONF_DEFAULT_UNIT
        self._unique_id = self.entity_id
        _LOGGER.debug("unique id : " + str(self._unique_id))
        self._device = device
        self._translation_key = translation_key

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
            self._attributes["lbs"] = float(self._value) / 0.453592
            if self._device.device_type == DeviceType.PROFILE:
                height = float(self._attributes.get(CONF_HEIGHT))
                inch = height / 2.54
                feet = math.floor(inch/12)
                inch = round(inch - 12 * feet, 1)
                self._attributes["height(ft/in)"] = str(feet) + "'" + str(inch) + '"'

                date_time_obj = datetime.strptime(self._attributes.get(CONF_BIRTH), "%Y-%m-%d")
                age = get_american_age(date_time_obj.strftime("%Y%m%d"), datetime.now().strftime('%Y%m%d'))
                _LOGGER.debug("age : " + str(age))
                self._attributes["age"] = age
                

                _LOGGER.debug("calc BMI - weight : " + str(self._value) + ", height : " + str(height))
                self._attributes[CONF_BMI] = float(self._value) / (float(height/100) * float(height/100))
            
    async def async_added_to_hass(self):
        value = self._device.configure.get(CONF_WEIGHT)
        _LOGGER.debug("async_added_to_hass - conf value : " + str(value))
        old_state = await self.async_get_last_sensor_data()
        _LOGGER.debug("last state : " + str(old_state))
        if old_state != None and old_state.native_value != None:
            value = old_state.native_value

        await self.async_set_value(value)
        #self._unit_of_measurement = old_state.native_unit_of_measurement

        # entity = er.async_get(self.hass).async_get(self.entity_id)
        # self._device.set_device_id(entity.device_id)
        # _LOGGER.debug("set device id : " + str(entity.device_id))
        
        await self.async_update_ha_state(True)

    def check_range(self, value: float) -> bool:
        return _in_range(float(value), float(self._value) - float(self._admit_range), float(self._value) + float(self._admit_range))

    async def async_set_value(self, value):
        state = self.hass.states.get(self._source_entity)
        if _is_valid_state(state):
            value = value * 0.453592 if state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) in ("lbs", "lb") else value
        self._value = value
        _LOGGER.debug("set native value : " + str(value))
        await self.calc_attribute()

        await self.async_update_ha_state(True)

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

    # @property
    # def name(self):
    #     """Return the name of the sensor."""
    #     return None if self._translation_key != None else self._name

    @property
    def device_class(self) -> str | None:
        return "weight"

    @property
    def state_class(self) -> SensorStateClass | str | None:
        return STATE_CLASS_MEASUREMENT

    @property
    def has_entity_name(self) -> bool:
        return True

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


