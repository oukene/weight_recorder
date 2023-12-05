import logging

from dataclasses import dataclass
from .const import *
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change
from homeassistant.components.sensor import (
    RestoreSensor, STATE_CLASS_MEASUREMENT,
)
from .hub import *
from .hub import _is_valid_state, _in_range

from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)

from operator import eq

from datetime import datetime
import math


_LOGGER = logging.getLogger(__name__)

ENTITY_ID_FORMAT = "sensor" + ".{}"



async def async_setup_entry(hass, entry, async_add_devices):
    """Add sensors for passed config_entry in HA."""
        
    new_devices = []
    hub = hass.data[DOMAIN][entry.entry_id]["hub"]
    devices = hub.devices

    for device_id, device in devices.items():
        #if device.device_type == DeviceType.PROFILE:
        for sensor_desc in SENSORS_DESC:
            if eq(device.device_type, DeviceType.HUB):
                if sensor_desc.key not in (SENSOR_KEY.WEIGHT.value, SENSOR_KEY.IMPEDANCE.value, SENSOR_KEY.STATUS.value):
                    continue
            elif device.device_type == DeviceType.PROFILE:
                if sensor_desc.key in (SENSOR_KEY.STATUS.value):
                    continue
            new_devices.append(WeightRecorderSensor(hass, entry.entry_id, device, sensor_desc),
        )

    for device_id, device in devices.items():
        if eq(device.device_type, DeviceType.PROFILE) and device.configure.get(CONF_USE_MI_BODY_SCALE_CARD_ENTITY):
            _LOGGER.debug("create mibody scale entity")
            new_devices.append(bodymiscale(hub, device))

    if new_devices:
        async_add_devices(new_devices)


class WeightRecorderSensor(EntityBase, RestoreSensor):
    """Representation of a Thermal Comfort Sensor."""

    _attr_state_class = STATE_CLASS_MEASUREMENT
    _attr_has_entity_name = True
    entity_description: WeightSensorEntityDescription

    def __init__(self, hass, entry_id, device, sensor_desc: SENSORS_DESC):
        """Initialize the sensor."""
        EntityBase.__init__(self, device, translation_key=sensor_desc.key)
        self._device: Device
        self.entry_id = entry_id
        self.entity_description = sensor_desc
        self.hass = hass
        self._hub = hass.data[DOMAIN][entry_id]["hub"]

        entity_name= device.configure.get(CONF_NAME)
        if sensor_desc.key == SENSOR_KEY.WEIGHT.value:
            self._admit_range = device.configure.get(CONF_ADMIT_WEIGHT_RANGE)
        elif sensor_desc.key == SENSOR_KEY.IMPEDANCE.value:
           self._admit_range = device.configure.get(CONF_ADMIT_IMP_RANGE)
        #elif sensor_desc.key == SENSOR_KEY.IMPEDANCE.value:
        #    self._admit_range = device.configure.get(CONF_ADMIT_IMP_RANGE)
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, "{}_{}".format(self._device.name, sensor_desc.key), current_ids="", hass=hass)
        #self._name = "{}".format(sensor_desc.key)
        self._value = None
        self._attributes = {}
        if self._device.device_type == DeviceType.PROFILE:
            self._attributes[ATTR_HEIGHT] = device.configure.get(CONF_HEIGHT)
            self._attributes[ATTR_BIRTH] = device.configure.get(CONF_BIRTH)

        self._device.set_sensor(self.entity_description.key, self)

        self._unit_of_measurement = sensor_desc.native_unit_of_measurement
        self._unique_id = self.entity_id
        self._device = device

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
        """"""
        # BMI calc
        if isNumber(self._value):
            self._attributes[ATTR_LBS] = float(self._value) / 0.453592
            if self._device.device_type == DeviceType.PROFILE:
                height = float(self._attributes.get(ATTR_HEIGHT))
                inch = height / 2.54
                feet = math.floor(inch/12)
                inch = round(inch - 12 * feet, 1)
                self._attributes[ATTR_HEIGHT_FEET_INCH] = str(feet) + "'" + str(inch) + '"'

                date_time_obj = datetime.strptime(self._attributes.get(CONF_BIRTH), "%Y-%m-%d")
                #age = get_american_age(date_time_obj.strftime("%Y%m%d"), datetime.now().strftime('%Y%m%d'))
                #_LOGGER.debug("age : " + str(age))
                #self._attributes[ATTR_AGE] = age
                

                _LOGGER.debug("calc BMI - weight : " + str(self._value) + ", height : " + str(height))
                bmi = float(self._value) / (float(height/100) * float(height/100))
                self._attributes[ATTR_BMI] = bmi
                bmi_state = None
                if bmi <= 18.5:
                    bmi_state = "under"
                elif bmi > 18.5 and bmi <= 25:
                    bmi_state = "normal"
                elif bmi > 25 and bmi <= 30:
                    bmi_state = "over"
                elif bmi > 30 and bmi <= 35:
                    bmi_state = "I_Obesity"
                elif bmi > 35 and bmi <= 40:
                    bmi_state = "II_Obesity"
                elif bmi > 40:
                    bmi_state = "III_Obesity"

                self._attributes[ATTR_BMI_STATE] = bmi_state
            
    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        value = None
        if self.entity_description.key == SENSOR_KEY.WEIGHT.value:
            value = self._device.configure.get(CONF_WEIGHT)
        old_state = await self.async_get_last_sensor_data()
        if old_state != None and old_state.native_value != None:
            value = old_state.native_value

        if self.entity_description.key == SENSOR_KEY.STATUS.value:
            value = "Ready"

        await self.async_set_value(value)
        #self._unit_of_measurement = old_state.native_unit_of_measurement

        # entity = er.async_get(self.hass).async_get(self.entity_id)
        # self._device.set_device_id(entity.device_id)
        # _LOGGER.debug("set device id : " + str(entity.device_id))
        #await self.async_update_ha_state(True)

        self._hub.add_weight_entity(self)

    def check_range(self, new_value) -> bool:
        if self._value == None or self._value == STATE_UNAVAILABLE or self._value == STATE_UNKNOWN or self._admit_range == None or self._value == 0:
            return True
        if self._value and self._admit_range:
            return _in_range(float(new_value), float(self._value) - float(self._admit_range), float(self._value) + float(self._admit_range))
        return False

    async def async_set_value(self, value):
        self._value = value
        if self.entity_description.display_precision:
            _LOGGER.debug(str(self._value))
            self._value = round(float(value), int(self.entity_description.display_precision))
        if self._device.device_type == DeviceType.PROFILE:
            if self.entity_description.attributes:
                _LOGGER.debug("configure : " + str(self._device.configure))
                _LOGGER.debug("value : " + str(self._value))
                if value != None:
                    self._attributes.update(self.entity_description.attributes(value, self._device.configure))

        if eq(self._device.device_type, DeviceType.PROFILE) and self._device.configure.get(CONF_USE_MI_BODY_SCALE_CARD_ENTITY):
            if self.entity_description.key == SENSOR_KEY.WEIGHT.value:
                self._hub.get_mibody_entity(self._device).set_extra_attribute("ideal", self._attributes.get("ideal", None))
            elif self.entity_description.key == SENSOR_KEY.BMI.value:
                self._hub.get_mibody_entity(self._device).set_extra_attribute("bmi_label", self._attributes.get("bmi_label", None))
            
            if self.entity_description.key == SENSOR_KEY.STATUS.value:
                self._hub.get_mibody_entity(self._device).set_extra_attribute("problem", "ok")
                self._hub.get_mibody_entity(self._device).set_state("ok")
            else:
                self._hub.get_mibody_entity(self._device).set_extra_attribute(self.entity_description.key, value)

        await self.async_update_ha_state(True)

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
        return self.entity_description.native_unit_of_measurement

    @property
    def suggested_display_precision(self) -> int | None:
        return self.entity_description.display_precision

    @property
    def icon(self) -> str | None:
        return self.entity_description.icon
