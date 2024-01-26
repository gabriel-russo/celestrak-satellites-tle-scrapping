from requests import get
from skyfield.iokit import parse_tle_file
from io import BytesIO
from pandas import DataFrame
from shapely.geometry import MultiPolygon


def convert_to_multipolygon(poly):
    if poly.geom_type == "Polygon":
        return MultiPolygon([poly])
    else:
        return poly


def remove_whitespace(text):
    return text.replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", "")


def decompose_tle(lines, ts=None, skip_names=False):
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


def tle_file(url, ts=None, skip_names=False):
    req = get(
        url,
        stream=True,
    )

    with BytesIO(req.content) as f:
        return list(parse_tle_file(f, ts, skip_names))


def celestrak_active_sat_tle_file(ts=None, skip_names=False):
    req = get("https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle")

    with BytesIO(req.content) as f:
        return DataFrame.from_records(list(decompose_tle(f, ts, skip_names)))


def celestrak_active_sat_json_file():
    return DataFrame.from_records(
        get(
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"
        ).json()
    )
