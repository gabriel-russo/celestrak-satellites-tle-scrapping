from datetime import datetime
from re import split
from typing import Generator, Optional
from shapely.geometry import Point
from skyfield.api import load, wgs84, EarthSatellite


def dms_to_dd(dms) -> float:
    try:
        deg, minutes, seconds, _ = split("[°'\"]", dms)
    except:
        deg, minutes, seconds = "0", "0", "0"

    return float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)


def get_satellite_lat_lng(
    line1: str, line2: str, at_datetime: datetime, name: Optional[str] = None
) -> dict:
    satellite = EarthSatellite(line1=line1, line2=line2, name=name, ts=load.timescale())
    geocentric = satellite.at(
        load.timescale().utc(
            at_datetime.year,
            at_datetime.month,
            at_datetime.day,
            at_datetime.hour,
            at_datetime.minute,
            at_datetime.second,
        )
    )

    position = wgs84.geographic_position_of(geocentric)

    lat = str(position.latitude).replace("deg", "°").replace(" ", "")
    lng = str(position.longitude).replace("deg", "°").replace(" ", "")
    elevation = position.elevation.m

    return {"lat": dms_to_dd(lat), "lng": dms_to_dd(lng), "elevation": float(elevation)}


def create_point(lat: float, lng: float, elevation: Optional[float] = None) -> Point:
    if elevation:
        return Point(lng, lat, elevation)
    return Point(lng, lat)
