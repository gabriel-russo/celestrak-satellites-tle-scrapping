from datetime import datetime, timezone
from io import BytesIO
from typing import TypedDict, Generator
from requests import get
from utils import decompose_tle


class CelestrakActiveSatellite(TypedDict):
    name: str
    line1: str
    line2: str
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


def get_active_satellites_tle(skip_names: bool = False) -> list[dict]:
    req = get("https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle")

    req.raise_for_status()

    with BytesIO(req.content) as f:
        tle = list(decompose_tle(f, skip_names))

    return tle


def get_active_satellites_data() -> list[dict]:
    req = get("https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json")

    req.raise_for_status()

    return req.json()


def celestrak_active_satellites() -> Generator[CelestrakActiveSatellite, None, None]:

    tle = get_active_satellites_tle()

    json = get_active_satellites_data()

    tle_index = {item["name"]: item for item in tle}

    for satellite in json:
        tle_data = tle_index.get(satellite["OBJECT_NAME"], None)

        if not tle_data:
            continue

        merged: CelestrakActiveSatellite = dict(
            name=satellite["OBJECT_NAME"],
            line1=tle_data["line1"],
            line2=tle_data["line2"],
            cospar_id=satellite["OBJECT_ID"],
            norad_id=satellite["NORAD_CAT_ID"],
            epoch=datetime.fromisoformat(satellite["EPOCH"]).replace(
                tzinfo=timezone.utc
            ),
            mean_motion=satellite["MEAN_MOTION"],
            eccentricity=satellite["ECCENTRICITY"],
            inclination=satellite["INCLINATION"],
            ra_of_asc_node=satellite["RA_OF_ASC_NODE"],
            arg_of_pericenter=satellite["ARG_OF_PERICENTER"],
            mean_anomaly=satellite["MEAN_ANOMALY"],
            ephemeris_type=satellite["EPHEMERIS_TYPE"],
            classification_type=satellite["CLASSIFICATION_TYPE"],
            element_set_no=satellite["ELEMENT_SET_NO"],
            rev_at_epoch=satellite["REV_AT_EPOCH"],
            bstar=satellite["BSTAR"],
            mean_motion_dot=satellite["MEAN_MOTION_DOT"],
            mean_motion_ddot=satellite["MEAN_MOTION_DDOT"],
        )

        yield merged
