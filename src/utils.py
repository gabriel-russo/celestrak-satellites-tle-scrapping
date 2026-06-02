"""
Utility functions for satellite data processing.
"""

from datetime import datetime
from re import split
from typing import Optional
from shapely.geometry import Point
from skyfield.api import load, wgs84, EarthSatellite


def dms_to_dd(dms) -> float:
    """
    Convert DMS (Degrees, Minutes, Seconds) coordinates to decimal degrees.

    Args:
        dms: A string containing the DMS coordinate in the format
              "DD°MM'SS.SSS''" or similar.

    Returns:
        float: The coordinate in decimal degrees.

    Notes:
        The function splits the DMS string by the degree (°), minute ('), and
        second (") characters, then calculates the decimal value by combining
        all components: degrees + minutes/60 + seconds/3600.

    Raises:
        Any exception occurs if the split fails (e.g., missing delimiters),
        in which case default values of "0" are used for deg, minutes, and seconds.
    """
    try:
        deg, minutes, seconds, _ = split("[°'\"]", dms)
    except:
        deg, minutes, seconds = "0", "0", "0"

    return float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)


def get_satellite_lat_lng(
    line1: str, line2: str, at_datetime: datetime, name: Optional[str] = None
) -> dict:
    """
    Calculate the geolocation (latitude, longitude, elevation) of a satellite
    at a specific datetime using the skyfield library.

    Args:
        line1: First line of the TLE (Two-Line Element Set).
        line2: Second line of the TLE.
        at_datetime: The datetime at which to calculate the satellite's position.
        name: Optional satellite name (used by skyfield for satellite identification).

    Returns:
        dict: A dictionary containing:
            - lat: Latitude in decimal degrees (converted from DMS format)
            - lng: Longitude in decimal degrees (converted from DMS format)
            - elevation: Elevation above the WGS84 ellipsoid in meters

    Notes:
        The function uses the skyfield library's EarthSatellite model to propagate
        the satellite's orbit and calculate its geocentric position at the given
        timestamp. The latitude and longitude are converted from DMS (Degrees,
        Minutes, Seconds) format to decimal degrees using the dms_to_dd helper
        function.
    """
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
    """
    Create a Shapely Point object representing a geographic location.

    Args:
        lat: Latitude in decimal degrees.
        lng: Longitude in decimal degrees.
        elevation: Optional elevation above the ellipsoid in meters.
                  If provided, creates a 3D Point; otherwise, creates a 2D Point.

    Returns:
        Point: A Shapely Point object representing the geographic location.

    Notes:
        Shapely Points are commonly used for geometric operations and spatial
        analysis of satellite trajectories. The elevation parameter is optional
        and is used for 3D spatial analysis when working with Earth's ellipsoidal
        coordinate system.
    """
    if elevation:
        return Point(lng, lat, elevation)
    return Point(lng, lat)
