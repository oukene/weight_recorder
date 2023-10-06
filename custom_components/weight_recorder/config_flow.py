"""Config flow for Hello World integration."""
import logging
import voluptuous as vol
from typing import Any, Dict, Optional
from datetime import datetime

import homeassistant.helpers.config_validation as cv

import homeassistant.helpers.entity_registry

from .const import *
from homeassistant.helpers import selector
from homeassistant import config_entries, exceptions
from homeassistant.core import callback

from homeassistant.helpers import (
    device_registry as dr,
    entity_platform,
    entity_registry as er,
)

import asyncio
import re

_LOGGER = logging.getLogger(__name__)

OPTION_ADD_PROFILE = "add profile"
OPTION_MODIFY_PROFILE = "modify profile"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH
    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self.data = user_input
            return self.async_create_entry(title=user_input[CONF_NAME], data=self.data)

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): cv.string,
                    #vol.Required(CONF_WEIGHT_ENTITY, default=None): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
                }), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Handle a option flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry
        self._selected_profile = None
        self._selected_conf = None
        self.data = {}
        self.data[CONF_WEIGHT_ENTITY] = config_entry.options.get(CONF_WEIGHT_ENTITY, None)
        self.data[TRANS_KEY_UNRECORDED_DATA] = config_entry.options.get(TRANS_KEY_UNRECORDED_DATA, {})
        self.data[CONF_USE_UNRECORDED_DATA] = config_entry.options.get(CONF_USE_UNRECORDED_DATA, False)
        self.data[CONF_ENTITIES] = config_entry.options.get(CONF_ENTITIES, {})

    async def remove_device(self, device_id):
        self.data[CONF_ENTITIES].clear()
        # remove device
        device_registry = dr.async_get(
            self.hass)
        device_registry.async_remove_device(device_id)

        entities = er.async_entries_for_config_entry(
            self._entity_registry, self.config_entry.entry_id)

        for e in entities:
            if e.device_id == device_id:
                self._entity_registry.async_remove(e.entity_id)
        
        devices = dr.async_entries_for_config_entry(
            self._device_registry, self.config_entry.entry_id)

        for e in entities:
            if conf := self.hass.states.get(e.entity_id).attributes.get(ATTR_CONF):
                self.data[CONF_ENTITIES][conf.get(CONF_NAME)] = conf


    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:

        errors: Dict[str, str] = {}

        self._entity_registry = er.async_get(self.hass)
        self._device_registry = dr.async_get(self.hass)

        entities = er.async_entries_for_config_entry(
            self._entity_registry, self.config_entry.entry_id)

        # for e in entities:
        #     _LOGGER.debug("entity info : " + str(e))

        if user_input is not None:
            if not errors:
                self.data[CONF_WEIGHT_ENTITY] = user_input.get(CONF_WEIGHT_ENTITY)
                self.data[CONF_USE_UNRECORDED_DATA] = user_input.get(CONF_USE_UNRECORDED_DATA)

                if user_input.get(CONF_OPTIONS_SELECT) == OPTION_ADD_PROFILE:
                    return await self.async_step_entity()
                elif user_input.get(CONF_OPTIONS_SELECT) == OPTION_MODIFY_PROFILE:
                    _LOGGER.debug("async step select")
                    return await self.async_step_select()
                else:
                    self.data["modifydatetime"] = datetime.now()
                    return self.async_create_entry(title=NAME, data=self.data)

        option_devices = []
        option_devices.append(OPTION_ADD_PROFILE)
        option_devices.append(OPTION_MODIFY_PROFILE)

        options_schema = vol.Schema(
            {
                vol.Required(CONF_WEIGHT_ENTITY, default=self.data.get(CONF_WEIGHT_ENTITY, None)): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
                vol.Optional(CONF_OPTIONS_SELECT): selector.SelectSelector(selector.SelectSelectorConfig(options=option_devices, mode=selector.SelectSelectorMode.LIST, translation_key="option_select")),
                vol.Optional(CONF_USE_UNRECORDED_DATA, default=self.data.get(CONF_USE_UNRECORDED_DATA, False)): selector.BooleanSelector(selector.BooleanSelectorConfig()),
                #vol.Optional(CONF_OPTIONS_SELECT): vol.In(option_devices),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )

    async def async_step_select(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a repo to watch."""
        self._selected_profile = None

        errors: Dict[str, str] = {}

        devices = dr.async_entries_for_config_entry(
            self._device_registry, self.config_entry.entry_id)

        # entities = homeassistant.helpers.entity_registry.async_entries_for_config_entry(
        #     self._entity_registry, self.config_entry.entry_id)

        if user_input is not None:
            if not errors:
                device_name = user_input[CONF_SELECT_DEVICE].split("-")[0]
                device_id = user_input[CONF_SELECT_DEVICE].split("-")[1]
                conf = self.data[CONF_ENTITIES].get(device_name)
                if conf == None:
                    for d in devices:
                        if d.name_by_user == device_name:
                            conf = self.data[CONF_ENTITIES].get(d.name)

                if user_input[CONF_DELETE_DEVICE]:
                    _LOGGER.debug("device id : " + str(device_id))
                    await self.remove_device(device_id)
                    # create entry
                    self.data["modifydatetime"] = datetime.now()
                    return self.async_create_entry(title=NAME, data=self.data)
                else:
                    # modify entity
                    self._selected_profile = device_id
                    self._selected_conf = conf
                    _LOGGER.debug("selected profile : " + str(self._selected_profile) + ", conf : " + str(conf))
                    return await self.async_step_entity()

        include_device = []
        # hub = self.hass.data[DOMAIN][self.config_entry.entry_id]["hub"]
        # for device_id, device in hub.devices.items():
        #     if not device.isHub():
        #         include_device.append(device.name + "-" + device.id)
        for d in devices:
            #if not d.isHub():
            if not re.search("_Hub", d.name):
                _LOGGER.debug("device info : " + str(d))
                include_device.append(d.name_by_user + "-" + d.id if d.name_by_user != None else d.name + "-" + d.id)

        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema(
                    {
                        vol.Required(CONF_SELECT_DEVICE, default=""): selector.SelectSelector(selector.SelectSelectorConfig(options=include_device, custom_value=False, 
                            mode=selector.SelectSelectorMode.DROPDOWN)),
                        vol.Optional(CONF_DELETE_DEVICE, default=False): selector.BooleanSelector(selector.BooleanSelectorConfig()),
                    }
            ), errors=errors
        )

    async def async_step_entity(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a repo to watch."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            if not errors:
                if self._selected_profile is not None and self._selected_conf is not None:
                    # modify device and entity
                    _LOGGER.debug("call async_update_device device id : " + str(self._selected_profile) + ", name : " + user_input[CONF_NAME])
                    #self._device_registry.async_update_device(self._selected_entity, name=user_input[CONF_NAME])

                    self.data[CONF_ENTITIES][self._selected_conf.get(CONF_NAME)][CONF_MODIFY_CONF] = {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_BIRTH: user_input[CONF_BIRTH],
                        CONF_HEIGHT: user_input.get(CONF_HEIGHT, 0),
                        CONF_WEIGHT: user_input.get(CONF_WEIGHT, 0),
                        CONF_ADMIT_RANGE: user_input[CONF_ADMIT_RANGE],
                        CONF_USE_MANUAL_INPUT: user_input[CONF_USE_MANUAL_INPUT],
                        "device_id": self._selected_profile,
                    }

                    # for conf in self.data[CONF_ENTITIES]:
                    #     if self._selected_conf.get(CONF_NAME) == conf.get(CONF_NAME):
                    #         conf[CONF_MODIFY_CONF] = {
                    #             CONF_NAME: user_input[CONF_NAME],
                    #             CONF_BIRTH: user_input[CONF_BIRTH],
                    #             CONF_HEIGHT: user_input[CONF_HEIGHT],
                    #             CONF_WEIGHT_ENTITY: user_input[CONF_WEIGHT_ENTITY],
                    #             CONF_HYSTERISIS: user_input[CONF_HYSTERISIS],
                    #         }

                    # entities = er.async_entries_for_config_entry(self._entity_registry, self.config_entry.entry_id)
                    # for e in entities:
                    #     if e.device_id == self._selected_entity:
                    #         self._entity_registry.async_update_entity(e.entity_id, original_name=)

                    #await self.remove_entity(self._selected_entity, self._selected_conf)
                else:
                    # append entity
                    self.data[CONF_ENTITIES][user_input[CONF_NAME]] = {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_BIRTH: user_input[CONF_BIRTH],
                        CONF_HEIGHT: user_input[CONF_HEIGHT],
                        CONF_WEIGHT: user_input[CONF_WEIGHT],
                        CONF_ADMIT_RANGE: user_input[CONF_ADMIT_RANGE],
                        CONF_USE_MANUAL_INPUT: user_input[CONF_USE_MANUAL_INPUT],
                    }

                self.data["modifydatetime"] = datetime.now()
                return self.async_create_entry(title=self.config_entry.data[CONF_NAME], data=self.data)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=self._selected_conf.get(CONF_NAME) if self._selected_conf is not None else None): cv.string,
                vol.Required(CONF_BIRTH, default=self._selected_conf.get(CONF_BIRTH) if self._selected_conf is not None else None): selector.TextSelector(selector.TextSelectorConfig(type="date")),
                vol.Required(CONF_HEIGHT, default=self._selected_conf.get(CONF_HEIGHT) if self._selected_conf is not None else 0): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=300, step=0.1, unit_of_measurement="cm", mode="slider")),
                vol.Required(CONF_WEIGHT, default=self._selected_conf.get(CONF_WEIGHT) if self._selected_conf is not None else 0): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=300, step=0.1, unit_of_measurement=CONF_DEFAULT_UNIT, mode="slider")),
                vol.Required(CONF_ADMIT_RANGE, default=self._selected_conf.get(CONF_ADMIT_RANGE) if self._selected_conf is not None else None): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=20, step=0.1, unit_of_measurement=CONF_DEFAULT_UNIT, mode="slider")),
                vol.Required(CONF_USE_MANUAL_INPUT, default=True): selector.BooleanSelector(selector.BooleanSelectorConfig()),
            }
        )
        return self.async_show_form(
            step_id="entity",
            data_schema=data_schema, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
