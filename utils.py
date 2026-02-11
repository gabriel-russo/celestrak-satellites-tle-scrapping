from re import split
from shapely.geometry import MultiPolygon, Point, LineString
from skyfield.api import load, wgs84, EarthSatellite


def dms_to_dd(dms) -> float:
    try:
        deg, minutes, seconds, _ = split("[°'\"]", dms)
    except:
        deg, minutes, seconds = "0", "0", "0"

    return float(deg) + float(minutes) / 60 + float(seconds) / (60 * 60)


def get_satellite_lat_lng(line1: str, line2: str, name: str, at_datetime) -> dict:
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
    # elevation = position.elevation.m

    return {"lat": dms_to_dd(lat), "lng": dms_to_dd(lng)}


def convert_to_multipolygon(poly):
    if poly.geom_type == "Polygon":
        return MultiPolygon([poly])
    else:
        return poly


def create_point(lat: float, lng: float) -> Point:
    return Point(lng, lat)


def create_linestring_from_points(points: list[Point]) -> LineString:
    if len(points) < 2:
        raise ValueError("A linestring must have at least 2 points")

    return LineString(points)


def decompose_tle(lines, ts=None, skip_names=False) -> dict:
    b0 = b1 = b""
    for b2 in lines:
        if (
            b2.startswith(b"2 ")
            and len(b2) >= 69
            and b1.startswith(b"1 ")
            and len(b1) >= 69
        ):
            if not skip_names and b0:
                b0 = b0.rstrip(b" \n\r")
                if b0.startswith(b"0 "):
                    b0 = b0[2:]  # Spacetrack 3-line format
                name = b0.decode("ascii")
            else:
                name = None

            line1 = b1.decode("ascii")
            line2 = b2.decode("ascii")
            yield {"name": name, "line1": line1, "line2": line2}

            b0 = b1 = b""
        else:
            b0 = b1
            b1 = b2
