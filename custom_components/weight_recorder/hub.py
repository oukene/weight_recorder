import copy
from datetime import datetime
import asyncio

from .const import *
from homeassistant.components.sensor import SensorExtraStoredData, RestoreSensor
from homeassistant.helpers.entity import Entity
import logging
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE, EVENT_HOMEASSISTANT_STARTED, ATTR_UNIT_OF_MEASUREMENT

from decimal import Decimal

from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
)

import time
from operator import eq

from custom_components.bodymiscale.metrics.scale import Scale
from custom_components.bodymiscale.metrics import get_body_type, get_fat_mass_to_ideal_weight
from homeassistant.helpers.entity import async_generate_entity_id


def get_american_age(birthday, thatday):
    _LOGGER.debug("birthday : " + str(birthday) +
                  ", thatday : " + str(thatday))
    this_year, today = int(thatday[:4]), thatday[4:]
    birth_year, birth_day = int(birthday[:4]), birthday[4:]
    my_age = this_year - birth_year

    if today < birth_day:
        my_age -= 1
    return my_age


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
    return state and state.state != STATE_UNKNOWN and state.state != STATE_UNAVAILABLE and state.state != None


def _in_range(n, start, end=0):
    return start <= n <= end if end >= start else end <= n <= start


_LOGGER = logging.getLogger(__name__)


class EntityBase(Entity):
    """Base representation of a Hello World Sensor."""

    should_poll = False
    _attr_has_entity_name = True

    def __init__(self, device, translation_key):
        """Initialize the sensor."""
        self._device = device
        self._translation_key = translation_key

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
    def translation_key(self) -> str | None:
        return self._translation_key

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._unique_id is not None:
            return self._unique_id

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return self._attributes


class bodymiscale(Entity):
    def __init__(self, hub, device):
        super().__init__()
        self._device = device
        self._hub = hub

        self.entity_id = async_generate_entity_id(
            "bodymiscale" + ".{}", "{}".format(device.name), current_ids="")

        self._hub.set_mibody_entity(device, self)
        self._attributes = {}
        self._attributes[CONF_HEIGHT] = self._device.configure.get(CONF_HEIGHT)
        self._attributes[CONF_GENDER] = self._device.configure.get(CONF_GENDER)

        date_time_obj = datetime.strptime(self._device.configure.get(CONF_BIRTH), "%Y-%m-%d")
        age = get_american_age(date_time_obj.strftime("%Y%m%d"), datetime.now().strftime('%Y%m%d'))
        self._attributes["age"] = int(age)
        self._attr_state = "ok"
        self._attributes["problem"] = "ok"

    def set_extra_attribute(self, key, value):
        _LOGGER.debug("set attribute ")

        if eq(key, SENSOR_KEY.METABOLIC_AGE.value):
            self._attributes[key] = int(value)
        else:
            self._attributes[key] = round(float(value), 2) if isNumber(value) else value

        if self._attributes.get(SENSOR_KEY.WEIGHT.value) and self._attributes.get(SENSOR_KEY.BODY_FAT.value) and self._attributes.get(SENSOR_KEY.MUSCLE_MASS.value) and self._attributes.get("height") and self._attributes.get("gender") and self._attributes.get("age"):
            scale = Scale(self._attributes.get("height"), self._attributes.get("gender"))
            config = {}
            config["scale"] = scale
            metrics = {}
            metrics[SENSOR_KEY.WEIGHT.value] = float(self._attributes.get(SENSOR_KEY.WEIGHT.value))
            metrics[SENSOR_KEY.BODY_FAT.value] = float(self._attributes.get(SENSOR_KEY.BODY_FAT.value))
            metrics[SENSOR_KEY.MUSCLE_MASS.value] = float(self._attributes.get(SENSOR_KEY.MUSCLE_MASS.value))
            metrics["age"] = int(self._attributes.get("age"))

            body_type = get_body_type(config, metrics)
            self._attributes["body_type"] = body_type

            ideal2weight = get_fat_mass_to_ideal_weight(config, metrics)
            if ideal2weight < 0:
                self._attributes["fat_mass_to_lose"] = round(ideal2weight * -1, 2)
            else:
                self._attributes["fat_mass_to_gain"] = round(ideal2weight, 2)

    @property
    def device_info(self):
        _LOGGER.debug("get device info")
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._device.device_id)},
            "name": self._device.name,
            "sw_version": self._device.firmware_version,
            "model": self._device.model,
            "manufacturer": self._device.manufacturer
        }

    @property
    def extra_state_attributes(self):
        return self._attributes

    def set_state(self, state):
        self._attr_state = state

    @property
    def state(self):
        """Return the state of the sensor."""
        # return self._state
        return self._attr_state


class Device:
    def __init__(self, hass, name, config, conf, device_type):
        self._id = f"{name}_{config.entry_id}"
        # self._id = f"{name}_{config.entry_id}"
        self._name = name
        self._name_by_user = None
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._conf = conf.get(CONF_MODIFY_CONF) if conf.get(
            CONF_MODIFY_CONF) else conf
        self.firmware_version = VERSION
        self.model = NAME
        self.manufacturer = MANUFACTURE
        self.__sensors = {}
        self._device_type = device_type

        if device_id := self.configure.get("device_id"):
            modify_device_name = self.configure.get(CONF_NAME)

            device_registry = dr.async_get(hass)
            _LOGGER.debug("set modify name device_id : " +
                          str(device_id) + ", name : " + str(modify_device_name))
            device_registry.async_update_device(
                device_id, name_by_user=modify_device_name)
            self._name_by_user = modify_device_name

    def isHub(self) -> bool:
        return self._device_type == DeviceType.HUB

    def set_device_id(self, id):
        self._id = id

    @property
    def device_type(self):
        return self._device_type

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

    def get_sensor(self, key):
        return self.__sensors.get(key)

    def set_sensor(self, key, entity):
        self.__sensors[key] = entity


class Hub:
    def __init__(self, hass, entry, weight_devices: dict) -> None:
        self.__devices = {}
        self.hass = hass
        self.entry = entry
        self._weight_devices = weight_devices
        self.last_weight = None
        self.__unrecorded_select_entity = None
        self.__profile_list_entity = None
        self.__weight_entities = {}
        self._recv_weight = False
        self._recv_imp = False
        self._current_id = 0
        self.__mibody_entity = {}
        self.setup()

    def get_mibody_entity(self, device):
        return self.__mibody_entity.get(device.name)

    def set_mibody_entity(self, device, entity):
        self.__mibody_entity[device.name] = entity

    def setup(self):
        for weight, devices in self._weight_devices.items():
            self.hass.data[DOMAIN][self.entry.entry_id]["listener"].append(
                async_track_state_change_event(self.hass, weight, self.entity_listener))
            if devices.get(CONF_IMP_ENTITY, None):
                self.hass.data[DOMAIN][self.entry.entry_id]["listener"].append(
                    async_track_state_change_event(self.hass, devices.get(CONF_IMP_ENTITY), self.imp_entity_listener))

        # self.hass.bus.async_listen_once(
        #    EVENT_HOMEASSISTANT_STARTED, self.hass_load_end)

    async def hass_load_end(self, event):
        """"""
        # self.hass.data[DOMAIN][self.entry.entry_id]["hass_loading"] = True
        # _LOGGER.debug("hass load end!!")
        # self._hass_load_end = True

    @callback
    async def imp_entity_listener(self, event: Event):
        entity = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        if _is_valid_state(new_state) and self._recv_weight:
            self._recv_imp = True
            self._last_imp_time = datetime.now().timestamp()

    @callback
    async def entity_listener(self, event: Event):
        entity = event.data["entity_id"]
        old_state = event.data["old_state"]
        new_state = event.data["new_state"]
        if not _is_valid_state(new_state) or Decimal(new_state.state) == Decimal(0) or self._recv_weight:
            # if not _is_valid_state(new_state) or self.last_weight == new_state.state or Decimal(new_state.state) == Decimal(0):
            return

        for device_id, device in self.devices.items():
            if device.device_type == DeviceType.HUB:
                self._recv_weight = True
                await device.get_sensor(SENSOR_KEY.STATUS.value).async_set_value("calculating...")
                await device.get_sensor(SENSOR_KEY.WEIGHT.value).async_set_value(new_state.state)
                await device.get_sensor(SENSOR_KEY.IMPEDANCE.value).async_set_value(0)

                remain_seconds = 7
                while (remain_seconds >= 0):
                    if self._recv_imp:
                        break
                    await asyncio.sleep(1)
                    await device.get_sensor(SENSOR_KEY.STATUS.value).async_set_value("remain " + str(remain_seconds) + "s")
                    remain_seconds = remain_seconds - 1
                await device.get_sensor(SENSOR_KEY.STATUS.value).async_set_value("Ready")
                break

        imp_value = 0
        if imp_entity := self._weight_devices[entity].get(CONF_IMP_ENTITY, None):
            imp_value = self.hass.states.get(imp_entity).state if _is_valid_state(
                self.hass.states.get(imp_entity)) and self._recv_imp else 0

        in_range_count = 0
        submit_device = None
        for device_id, device in self.devices.items():
            if device and device.get_sensor(SENSOR_KEY.WEIGHT.value):
                if device.device_type == DeviceType.HUB:
                    # await device.get_sensor(SENSOR_KEY.WEIGHT.value).async_set_value(new_state.state)
                    await device.get_sensor(SENSOR_KEY.IMPEDANCE.value).async_set_value(imp_value)
                    self.last_weight = new_state.state
                    # await device.get_sensor(SENSOR_KEY.IMPEDANCE.value).async_set_value(bia_valbbue)
                    continue
                elif device.device_type == DeviceType.PROFILE:
                    _LOGGER.debug("check check range")
                    _LOGGER.debug("old_state : " + str(old_state))
                    _LOGGER.debug("new_state : " + str(new_state))
                    if device.get_sensor(SENSOR_KEY.WEIGHT.value).check_range(new_state.state) \
                            and (imp_value == 0 or device.get_sensor(SENSOR_KEY.IMPEDANCE.value).check_range(imp_value)):
                        in_range_count += 1
                        submit_device = device

        find_selected_profile = False
        _LOGGER.debug("in range count: " + str(in_range_count))
        if self.profile_list_entity != None:
            for entity_id, profile in self.profile_list_entity._profiles.items():
                if profile == self.profile_list_entity.current_option:
                    for device_id, device in self.devices.items():
                        if entity_id == device.get_sensor(SENSOR_KEY.WEIGHT.value).entity_id:
                            _LOGGER.debug("find selected profile")
                            await self.record_user_profile(
                                device, float(new_state.state), "kg", imp_value)
                            find_selected_profile = True
        if find_selected_profile == False:
            if in_range_count == 1:
                await self.record_user_profile(submit_device, new_state.state, new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT), imp_value)
            else:
                # unrecorded data process
                if self.unrecorded_entity:
                    await self.unrecorded_entity.async_add_option(new_state.state, imp_value)

        self._recv_imp = False
        self._recv_weight = False
        if self.profile_list_entity:
            await self.profile_list_entity.async_select_option("-")
        # for device_id, device in self.devices.items():
        #     if device.device_type == DeviceType.HUB:
        #         await device.get_sensor(SENSOR_KEY.STATUS.value).async_set_value("Ready")
        # if in_range_count == 1:
        # await self.record_user_profile(submit_device, new_state.state, new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT), imp_value)
        # await submit_device.get_sensor(SENSOR_KEY.WEIGHT.value).async_set_value(new_state.state, new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT))
        # else:
        #     _LOGGER.debug("check selected profile")
        #     if self.profile_list_entity != None:
        #         for entity_id, profile in self.profile_list_entity._profiles.items():
        #             if profile == self.profile_list_entity.current_option:
        #                 for device_id, device in self.devices.items():
        #                     if entity_id == device.get_sensor(SENSOR_KEY.WEIGHT.value).entity_id:
        #                         _LOGGER.debug("find selected profile")
        #                         await self.record_user_profile(
        #                             device, float(new_state.state), "kg", imp_value)
        #                         return
        #     # unrecorded data process
        #     if self.unrecorded_entity:
        #         await self.unrecorded_entity.async_add_option(new_state.state, imp_value)

    def add_device(self, device: Device) -> None:
        self.__devices[device.device_id] = device

    def add_weight_entity(self, entity):
        self.__weight_entities[entity.entity_id] = entity

    @property
    def profile_list_entity(self):
        return self.__profile_list_entity

    @profile_list_entity.setter
    def profile_list_entity(self, entity):
        self.__profile_list_entity = entity

    @property
    def unrecorded_entity(self):
        return self.__unrecorded_select_entity

    @unrecorded_entity.setter
    def unrecorded_entity(self, entity):
        self.__unrecorded_select_entity = entity

    @property
    def weight_entities(self) -> list[str]:
        entities = []
        for device_id, device in self.devices.items():
            if not device.isHub():
                entities.append(device.weight_entity.entity_id +
                                "-" + device.name)

        return entities

    @property
    def device(self, device_id: str) -> Device:
        return self.__devices.get(device_id, None)

    @property
    def devices(self) -> dict[str, Device]:
        return self.__devices

    @devices.setter
    def devices(self, devices):
        self.__devices = devices

    async def record_user_profile(self, device: Device, weight: float, unit, imp):
        # profile_entity.async_set_value(weight, unit)
        weight = weight * 0.453592 if unit in ("lbs", "lb") else weight
        # body = BodyCalculator(weight, device.configure.get(CONF_HEIGHT), device.configure.get(CONF_GENDER), device.configure.get(CONF_BIRTH), imp)
        # result = body.get_result()

        _LOGGER.debug("device conf : " + str(device.configure))

        conf = copy.deepcopy(device.configure)
        scale = Scale(conf.get(CONF_HEIGHT), conf.get(CONF_GENDER))
        conf["scale"] = scale
        date_time_obj = datetime.strptime(conf.get(CONF_BIRTH), "%Y-%m-%d")
        age = get_american_age(date_time_obj.strftime("%Y%m%d"), datetime.now().strftime('%Y%m%d'))

        if imp == 0:
            if last_imp := device.get_sensor(SENSOR_KEY.IMPEDANCE.value).state:
                if last_imp != STATE_UNAVAILABLE and last_imp != STATE_UNKNOWN:
                    imp = last_imp

        metrics = {}
        metrics[CONF_WEIGHT] = float(weight)
        metrics["age"] = int(age)
        metrics["impedance"] = float(imp)

        for desc in SENSORS_DESC:
            if desc.key == SENSOR_KEY.WEIGHT.value:
                await device.get_sensor(desc.key).async_set_value(weight)
            elif desc.key == SENSOR_KEY.IMPEDANCE.value:
                await device.get_sensor(desc.key).async_set_value(imp)
            elif desc.key == SENSOR_KEY.LAST_RECORD_TIME.value:
                date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                await device.get_sensor(desc.key).async_set_value(date)
            elif desc.key != SENSOR_KEY.STATUS.value and imp != 0:
                result = desc.calculator(conf, metrics)
                metrics[desc.key] = float(result)

                await device.get_sensor(desc.key).async_set_value(float(result))
        """"""

    async def record_data(self):
        """"""
        time = self.unrecorded_entity.current_option.split(",")[0]
        weight = self.unrecorded_entity.current_option.split(",")[1]
        imp = self.unrecorded_entity.current_option.split(",")[2]

        for entity_id, profile in self.profile_list_entity._profiles.items():
            if profile == self.profile_list_entity.current_option:
                for device_id, device in self.devices.items():
                    if entity_id == device.get_sensor(SENSOR_KEY.WEIGHT.value).entity_id:
                        await self.record_user_profile(
                            device, float(weight), "kg", imp)
                        await self.remove_data()
                        break

    async def remove_data(self):
        """"""
        time = self.unrecorded_entity.current_option.split(",")[0]
        await self.unrecorded_entity.async_remove_option(time)

    async def clear_data(self):
        """"""
        await self.unrecorded_entity.async_clear_option()
