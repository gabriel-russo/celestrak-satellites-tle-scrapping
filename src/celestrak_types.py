from datetime import datetime
from typing import TypedDict


class SatelliteJSON(TypedDict):
    """
    Dictionary representing satellite data in JSON format as provided by Celestrak.

    The parameters are Keplerian elements (orbital elements) from the TLE
    (Two-Line Element Set) element set.

    Fields:
        OBJECT_NAME: Official name of the object/satellite
        OBJECT_ID: COSPAR identifier of the satellite
        EPOCH: Time of element (UTC in YYYY-MM-DD HH:MM:SS format)
        MEAN_MOTION: Mean motion (revolutions per day around Earth)
        ECCENTRICITY: Orbital eccentricity (0-1)
        INCLINATION: Orbital inclination (degrees)
        RA_OF_ASC_NODE: Right ascension of the ascending node (degrees)
        ARG_OF_PERICENTER: Argument of perigee (degrees)
        MEAN_ANOMALY: Mean anomaly (degrees)
        EPHEMERIS_TYPE: Ephemeris type (0-2)
        CLASSIFICATION_TYPE: Object classification (0: U=Civil, 1: M=Military, etc.)
        NORAD_CAT_ID: NORAD catalog number (unique identifier)
        ELEMENT_SET_NO: Element number (usually 1 or 2)
        REV_AT_EPOCH: Revolutions since reference epoch (elements 4-5)
        BSTAR: BSTAR factor (0-1) (elements 6-9)
        MEAN_MOTION_DOT: First derivative of mean motion (elements 10-11)
        MEAN_MOTION_DDOT: Second derivative of mean motion (elements 10-11)
    """

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
    """
    Dictionary representing raw two-line TLE (Two-Line Element Set) data
    for a satellite, as formatted by Celestrak.

    A TLE is a data set that describes the approximate position of objects in
    Earth orbit. The two lines contain orbital parameters sufficient to calculate
    the satellite's position at any future time (up to a certain accuracy limit).

    Fields:
        name: Name of the satellite/object
        line1: First line of the TLE (line of elements)
        line2: Second line of the TLE (line of elements)
    """

    name: str
    line1: str
    line2: str


class Satellite(SatelliteTLE):
    """
    Dictionary representing a complete satellite with all TLE information
    expanded, including processed data and additional fields.

    This class inherits from SatelliteTLE and adds detailed orbital parameters
    such as Keplerian elements, epoch data, and perturbation parameters, as defined
    by the Celestrak TLE standard.

    Fields inherited from SatelliteTLE:
        name: Name of the satellite/object
        line1: First line of the TLE (line of elements)
        line2: Second line of the TLE (line of elements)

    Additional fields:
        cospar_id: COSPAR identifier of the satellite (e.g., 2024-001A)
        norad_id: NORAD catalog number (unique object identifier)
        epoch: Time of validity for the orbital elements (UTC)
        mean_motion: Mean motion of the satellite in revolutions per day
        eccentricity: Orbital eccentricity (0 = circular orbit)
        inclination: Orbital inclination in degrees
        ra_of_asc_node: Right ascension of the ascending node in degrees
        arg_of_pericenter: Argument of perigee in degrees
        mean_anomaly: Mean anomaly in degrees (satellite position in orbit)
        ephemeris_type: Ephemeris type (0=propagated, 1=observed, 2=telescopic)
        classification_type: Object classification (0=Civil, 1=Military, etc.)
        element_set_no: Element number (usually 1 or 2)
        rev_at_epoch: Number of revolutions since reference epoch (J2000 period)
        bstar: BSTAR factor used to model atmospheric drag
        mean_motion_dot: First derivative of mean motion (rate of mean motion change)
        mean_motion_ddot: Second derivative of mean motion (rate of acceleration change)
    """

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
