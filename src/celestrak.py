from datetime import datetime, timezone
from typing import Generator
from celestrak_types import Satellite, SatelliteJSON
from requests import get
from tle import satellite_to_tle


def get_active_satellites_data() -> list[SatelliteJSON]:
    req = get("https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json")

    req.raise_for_status()

    return req.json()


def celestrak_active_satellites() -> Generator[Satellite, None, None]:

    json_data = get_active_satellites_data()

    for satellite in json_data:
        tle = satellite_to_tle(satellite)

        merged: Satellite = {
            "name": satellite["OBJECT_NAME"],
            "line1": tle["line1"],
            "line2": tle["line2"],
            "cospar_id": satellite["OBJECT_ID"],
            "norad_id": satellite["NORAD_CAT_ID"],
            "epoch": datetime.fromisoformat(satellite["EPOCH"]).replace(
                tzinfo=timezone.utc
            ),
            "mean_motion": satellite["MEAN_MOTION"],
            "eccentricity": satellite["ECCENTRICITY"],
            "inclination": satellite["INCLINATION"],
            "ra_of_asc_node": satellite["RA_OF_ASC_NODE"],
            "arg_of_pericenter": satellite["ARG_OF_PERICENTER"],
            "mean_anomaly": satellite["MEAN_ANOMALY"],
            "ephemeris_type": satellite["EPHEMERIS_TYPE"],
            "classification_type": satellite["CLASSIFICATION_TYPE"],
            "element_set_no": satellite["ELEMENT_SET_NO"],
            "rev_at_epoch": satellite["REV_AT_EPOCH"],
            "bstar": satellite["BSTAR"],
            "mean_motion_dot": satellite["MEAN_MOTION_DOT"],
            "mean_motion_ddot": satellite["MEAN_MOTION_DDOT"],
        }

        yield merged
