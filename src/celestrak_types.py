from datetime import datetime
from typing import TypedDict


class SatelliteJSON(TypedDict):
    OBJECT_NAME: str
    OBJECT_ID: str
    EPOCH: str
    MEAN_MOTION: float
    ECCENTRICITY: float
    INCLINATION: float
    RA_OF_ASC_NODE: float
    ARG_OF_PERICENTER: float
    MEAN_ANOMALY: float
    EPHEMERIS_TYPE: int
    CLASSIFICATION_TYPE: str
    NORAD_CAT_ID: int
    ELEMENT_SET_NO: int
    REV_AT_EPOCH: int
    BSTAR: float
    MEAN_MOTION_DOT: float
    MEAN_MOTION_DDOT: float


class SatelliteTLE(TypedDict):
    name: str
    line1: str
    line2: str


class Satellite(SatelliteTLE):
    cospar_id: str
    norad_id: int
    epoch: datetime
    mean_motion: float
    eccentricity: float
    inclination: float
    ra_of_asc_node: float
    arg_of_pericenter: float
    mean_anomaly: float
    ephemeris_type: int
    classification_type: str
    element_set_no: int
    rev_at_epoch: int
    bstar: float
    mean_motion_dot: float
    mean_motion_ddot: float
