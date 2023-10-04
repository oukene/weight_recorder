"""Constants for the Detailed Hello World Push integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "weight_recorder"
NAME = "Weight Recorder"
VERSION = "1.0.0"
MANUFACTURE = "oukene"

CONF_WEIGHT_ENTITY = "weight_entity"
CONF_NAME = "device_name"
CONF_SOURCE_ENTITY = "origin_entity"

CONF_COUNT_WAIT_TIME = "count_wait_time"
CONF_CONTINUOUS_TIMER = "continuous_timer"

CONF_ENTITIES = "entities"
CONF_ADD_ANODHER = "add_another"
CONF_NAME = "name"
CONF_MAX_COUNT = "count_max"

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

ATTR_CONF = "configure"

CONF_ENTITY_STATE = "entity_state"
CONF_OPERATOR = "operator"
CONF_COUNT_VALUE = "count_value"
CONF_STATE = "state"


NUMBER_MIN = 0
NUMBER_MAX = 10

EQUAL = "equal"
NOT_EQUAL = "not equal"
BIGGER_THAN = "bigger than"
SMALLER_THAN = "smaller than"


OPERATOR_TYPES = [
    EQUAL,
    NOT_EQUAL,
    BIGGER_THAN,
    SMALLER_THAN
]