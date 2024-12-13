
from enum import Enum
from homeassistant.components.sensor import (
    SensorStateClass, SensorEntityDescription, SensorDeviceClass,
    SensorStateClass
)
from dataclasses import dataclass
from enum import StrEnum

from custom_components.bodymiscale.metrics.scale import Scale
from custom_components.bodymiscale.metrics.body_score import get_body_score
from custom_components.bodymiscale.metrics.weight import get_bmr, get_bmi, get_visceral_fat
from custom_components.bodymiscale.metrics.impedance import get_bone_mass, get_lbm, get_metabolic_age, get_muscle_mass, get_protein_percentage, get_water_percentage, get_fat_percentage
from custom_components.bodymiscale.util import get_bmi_label, get_ideal_weight
from custom_components.bodymiscale.const import ATTR_BMILABEL, ATTR_IDEAL

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "weight_recorder"
NAME = "Weight Recorder"
VERSION = "1.0.5"
MANUFACTURE = "oukene"

TRANS_KEY_MANUAL_INPUT_WEIGHT = "manual_input_weight"
TRANS_KEY_MANUAL_INPUT_HEIGHT = "manual_input_height"
TRANS_KEY_UNRECORDED_DATA = "unrecorded_data"
TRANS_KEY_PROFILE_LIST = "profile_list"
TRANS_KEY_UNRECORDED_INPUT = "unrecorded_input"
TRANS_KEY_UNRECORDED_REMOVE = "unrecorded_remove"
TRANS_KEY_UNRECORDED_CLEAR = "unrecorded_clear"


CONF_GENDER = "gender"
GENDER = [
    "female",
    "male",
]

CONF_WEIGHT_ENTITY = "weight_entity"
CONF_IMP_ENTITY = "imp_entity"
CONF_DEVICE_TYPE = "device_type"
CONF_SELECT_PROFILE_RESET_SECONDS = "select_profile_reset_seconds"

CONF_WEIGHT_DEVICES = "weight_devices"
CONF_PROFILES = "profiles"
CONF_NAME = "name"
CONF_USE_UNRECORDED_DATA = "use_unrecorded_data"
CONF_OPTIONS_SELECT = "options_select"
CONF_SELECT_DEVICE = "select_device"
CONF_DELETE_DEVICE = "delete_device"
CONF_ADMIT_WEIGHT_RANGE = "admit_weight_range"
CONF_ADMIT_IMP_RANGE = "admit_imp_range"
CONF_MODIFY_CONF = "modify_conf"
CONF_BIRTH = "birth"
CONF_HEIGHT = "height"
CONF_WEIGHT = "weight"
CONF_BMI = "bmi"
CONF_DEFAULT_ENTITY_NAME = "weight"
CONF_USE_MANUAL_INPUT = "manual_input"
CONF_USE_MI_BODY_SCALE_CARD_ENTITY = "use_mibodyscalecard_entity"

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


@dataclass
class WeightSensorEntityDescription(
    SensorEntityDescription
):
    calculator: str | None = None
    display_precision: int | None = None
    attributes: dict | None = None


class SENSOR_KEY(Enum):
    WEIGHT = "weight"
    HEIGHT = "height"
    IMPEDANCE = "impedance"
    BASAL_METABOLISM = "basal_metabolism"
    BODY_FAT = "body_fat"
    BMI = "bmi"
    BODY_SCORE = "body_score"
    BONE_MASS = "bone_mass"
    LEAN_BODY_MASS = "lean_body_mass"
    METABOLIC_AGE = "metabolic_age"
    MUSCLE_MASS = "muscle_mass"
    PROTEIN = "protein"
    WATER = "water"
    VISCERAL_FAT = "visceral_fat"
    STATUS = "status"
    LAST_RECORD_TIME = "last_record_time"


SENSORS_DESC = [
    WeightSensorEntityDescription(
        key=SENSOR_KEY.STATUS.value,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.WEIGHT.value,
        native_unit_of_measurement="kg",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        display_precision=2,
        attributes=lambda _, config: {ATTR_IDEAL: get_ideal_weight(config)},
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.HEIGHT.value,
        native_unit_of_measurement="cm",
        icon="mdi:human-male-height-variant",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        display_precision=1,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.IMPEDANCE.value,
        native_unit_of_measurement="Ω",
        icon="mdi:omega",
        state_class=SensorStateClass.MEASUREMENT,
        display_precision=0,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.BASAL_METABOLISM.value,
        native_unit_of_measurement="kcal",
        # device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        calculator=get_bmr,
        display_precision=2,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.BMI.value,
        # state_class=SensorStateClass.MEASUREMENT,
        calculator=get_bmi,
        display_precision=2,
        attributes=lambda state, _: {ATTR_BMILABEL: get_bmi_label(state)},
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.LEAN_BODY_MASS.value,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement="kg",
        calculator=get_lbm,
        display_precision=2,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.BODY_FAT.value,
        native_unit_of_measurement="%",
        # state_class=SensorStateClass.MEASUREMENT,
        calculator=get_fat_percentage,
        display_precision=0,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.BONE_MASS.value,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WEIGHT,
        calculator=get_bone_mass,
        native_unit_of_measurement="kg",
        display_precision=2,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.METABOLIC_AGE.value,
        state_class=SensorStateClass.MEASUREMENT,
        calculator=get_metabolic_age,
        display_precision=0,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.MUSCLE_MASS.value,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.WEIGHT,
        calculator=get_muscle_mass,
        native_unit_of_measurement="kg",
        display_precision=2,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.WATER.value,
        native_unit_of_measurement="%",
        icon = "mdi:water",
        state_class=SensorStateClass.MEASUREMENT,
        calculator=get_water_percentage,
        display_precision=0,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.PROTEIN.value,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        calculator=get_protein_percentage,
        display_precision=0,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.VISCERAL_FAT.value,
        state_class=SensorStateClass.MEASUREMENT,
        calculator=get_visceral_fat,
        display_precision=2,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.BODY_SCORE.value,
        native_unit_of_measurement="point",
        state_class=SensorStateClass.MEASUREMENT,
        icon = "mdi:medal",
        calculator=get_body_score,
        display_precision=0,
    ),
    WeightSensorEntityDescription(
        key=SENSOR_KEY.LAST_RECORD_TIME.value,
        icon="mdi:clock",
    )
]
