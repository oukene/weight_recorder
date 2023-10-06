"""Constants for the Detailed Hello World Push integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from enum import Enum

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "weight_recorder"
NAME = "Weight Recorder"
VERSION = "1.0.0"
MANUFACTURE = "oukene"

TRANS_KEY_WEIGHT = "weight"
TRANS_KEY_MANUAL_INPUT = "manual_input"
TRANS_KEY_UNRECORDED_DATA = "unrecorded_data"
TRANS_KEY_PROFILE_LIST = "profile_list"
TRANS_KEY_UNRECORDED_INPUT = "unrecorded_input"
TRANS_KEY_UNRECORDED_REMOVE = "unrecorded_remove"
TRANS_KEY_UNRECORDED_CLEAR = "unrecorded_clear"


CONF_WEIGHT_ENTITY = "weight_entity"
CONF_ENTITIES = "entities"
CONF_NAME = "name"
CONF_USE_UNRECORDED_DATA = "use_unrecorded_data"
CONF_OPTIONS_SELECT = "options_select"
CONF_SELECT_DEVICE = "select_device"
CONF_DELETE_DEVICE = "delete_device"
CONF_ADMIT_RANGE = "admit_range"
CONF_MODIFY_CONF = "modify_conf"
CONF_BIRTH = "birth"
CONF_HEIGHT = "height"
CONF_WEIGHT = "weight"
CONF_BMI = "bmi"
CONF_DEFAULT_UNIT = "kg"
CONF_DEFAULT_ENTITY_NAME = "weight"
CONF_USE_MANUAL_INPUT = "manual_input"

ATTR_CONF = "configure"

ATTR_BMI = "bmi"
ATTR_BMI_STATE = "bmi_state"
ATTR_HEIGHT_FEET_INCH = "height(ft/in)"
ATTR_HEIGHT = "height"
ATTR_AGE = "age"
ATTR_LBS = "lbs"
ATTR_BIRTH = "birth"


class DeviceType(Enum):
    PROFILE = 0,
    HUB = 1



