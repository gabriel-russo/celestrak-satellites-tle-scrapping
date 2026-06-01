from datetime import datetime
from typing import TypeAlias, Union
from math import floor, log10
from decimal import Decimal, ROUND_HALF_UP
from celestrak_types import SatelliteTLE, SatelliteJSON

number: TypeAlias = Union[int, float]


def format_float_str(val: number | str, total_width: int, dec_digits: int) -> str:
    """
    Ensures floating-point numbers are converted into strings with exact
    total widths and decimal places, strictly enforcing traditional mathematical
    rounding.

    Args:
        val: The numerical value to be formatted.
        total_width: The exact total width of the resulting string (including padding spaces).
        dec_digits: The precise number of decimal places after the radix point.

    Notes:
        **Implementation Note:** This function overrides Python's default string formatting (e.g., `f"{val:.4f}"`) by forcing a `ROUND_HALF_UP` behavior via the native `decimal` module. This prevents tie-breaking values (ending exactly in `.5`) from undergoing *Banker's Rounding* (rounding to the nearest even number), which would otherwise corrupt the line's final checksum.
    """
    d = Decimal(str(val)).quantize(
        Decimal("1." + "0" * dec_digits), rounding=ROUND_HALF_UP
    )
    return f"{d:{total_width}.{dec_digits}f}"


def format_sci(val: number) -> str:
    """
    Formats numerical values into the strict 8-character pseudo-scientific notation
    required for the **BSTAR** and **MEAN_MOTION_DDOT** fields.

    Args:
        val: The numerical value to be formatted.

    Notes:
        * **Behavior:** Converts a decimal value into a 5-digit mantissa preceded by a
            sign, followed immediately by the exponent's sign and a single-digit base-10 exponent
            (e.g., `0.0001` becomes ` 10000-4`).
        * **Edge Case Handling:** If the mantissa rounding triggers an overflow (e.g., `>= 100000`),
            the function applies a *clamp*, resetting the mantissa to `10000` and incrementing the exponent by 1.
    """
    if val == 0:
        return " 00000+0"
    sign = "-" if val < 0 else " "
    v = abs(val)
    exp = int(floor(log10(v))) + 1

    # Usa Decimal para arredondar a mantissa corretamente
    mantissa_float = v * 10 ** (5 - exp)
    mantissa = int(
        Decimal(str(mantissa_float)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )

    # Clamp caso o arredondamento estoure a base
    if mantissa >= 100000:
        mantissa = 10000
        exp += 1

    exp_sign = "+" if exp >= 0 else "-"
    return f"{sign}{mantissa:05d}{exp_sign}{abs(exp)}"


def format_ndot(val: number) -> str:
    """
    Formats the `MEAN_MOTION_DOT` parameter (First Derivative of Mean Motion) by
    completely omitting the leading zero before the decimal point.
    Args:
        val: The numerical value to be formatted.
    Notes:
        * **Output Format:** A leading space or minus sign, followed directly by the decimal
            point and exactly 8 decimal digits (e.g., `0.00001234` becomes ` .00001234`, and `-0.00001234` becomes `-.00001234`).
    """
    d = Decimal(str(val)).quantize(Decimal(".00000001"), rounding=ROUND_HALF_UP)
    s = f"{d: .8f}"
    if s.startswith(" 0."):
        return " ." + s[3:]
    elif s.startswith("-0."):
        return "-." + s[3:]
    return s


def format_epoch(epoch_str: str) -> str:
    """
    Converts a UTC date-time string in ISO format into the standard TLE epoch representation.
    Args:

    Notes:
        * **Mechanism:** Extracts the last two digits of the year and calculates the ordinal
            day of that year, appended with the fractional part of the day calculated down to a
            precision of 8 decimal places.
        * **Fine-Tuning:** The fractional day is rounded independently using mathematical rounding
            before dropping its leading `0`, ensuring that microsecond adjustments don't cause
            cascading day-count roll-overs.
    """
    dt = datetime.fromisoformat(epoch_str)
    year = dt.year % 100
    day_of_year = dt.timetuple().tm_yday
    sec_of_day = dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
    fraction = sec_of_day / 86400.0

    fraction_d = Decimal(str(fraction)).quantize(
        Decimal(".00000001"), rounding=ROUND_HALF_UP
    )
    fraction_str = f"{fraction_d:.8f}"[1:]  # Remove o '0' inicial
    return f"{year:02d}{day_of_year:03d}{fraction_str}"


def format_eccentricity(val: number) -> str:
    """
    Formats orbital eccentricity into a strict 7-column fixed string.

    Args:
        val: The numerical value to be formatted.

    Notes:
        * **Dropping the Radix:** The TLE standard implicitly assumes that eccentricity always starts with `0.`,
            also this function strips the first two characters from the formatted string.
        * **Strict Boundary Clamping:** If the input eccentricity is extremely close to 1.0 (e.g., `0.99999996`),
            a standard floating-point round forces the value to `1.0000000`. Since standard TLEs are strictly reserved
            for elliptical or circular orbits (where eccentricity must be less than 1.0), the function intercepts this
            behavior and forces the absolute ceiling value: `"9999999"`.
    """
    if val < 0:
        val = 0.0
    d = Decimal(str(val)).quantize(Decimal(".0000001"), rounding=ROUND_HALF_UP)

    # Evita a falha '0000000' quando o float arredonda para 1.0
    if d >= Decimal("1.0000000"):
        return "9999999"

    s = f"{d:.7f}"
    return s[2:]


def format_id(obj_id: str) -> str:
    """
    Formats the International Designator / COSPAR ID extracted from the `OBJECT_ID` field.

    Args:
        obj_id: Satellite COSPAR ID / OBJECT_ID.
    Notes:
        * **Mechanism:** Splits a string like `"2020-025A"` to extract the modified launch year (last two digits)
            and the launch piece piece-code. It then left-aligns the piece code, padding it with spaces to fit the rigid 8-character block.
    """
    parts = obj_id.split("-")
    year = int(parts[0]) % 100
    piece = parts[1]
    return f"{year:02d}{piece:<6}"[:8]


def calc_checksum(line: str) -> str:
    """
    Computes the remainder of 10 checksum digit positioned at the very end (column 69) of any given TLE line.

    Args:
        line: TLE line
    Notes:
        * **Rules:** Iterates through every character in the string, summing up all individual digits.
            Non-numeric characters are skipped entirely, with the sole exception of the minus sign (`-`), which adds a value of 1 to the tally. The final checksum is the remainder of this grand total divided by 10.
    """
    return str(
        sum((int(c) if c.isdigit() else (1 if c == "-" else 0)) for c in line) % 10
    )


def satellite_to_tle(satellite_dict: SatelliteJSON) -> SatelliteTLE:
    """
    Convert Celestrak satellite JSON to satellite TLE.

    Args:
        satellite_dict: A dictionary containing raw orbital parameters retrieved from Celestrak/NORAD.

    Notes:
        * The execution flow follows three structural steps:
            1 - Individual processing and formatting of each orbital parameter using specialized nested helper functions.
            2 - Building **Line 1** and computing its respective trailing checksum digit.
            3 - Building **Line 2** and computing its respective trailing checksum digit.
    """

    # --- Build line 1 ---
    cat = satellite_dict["NORAD_CAT_ID"]
    clas = satellite_dict["CLASSIFICATION_TYPE"]
    obj_id = format_id(satellite_dict["OBJECT_ID"])
    epoch = format_epoch(satellite_dict["EPOCH"])
    ndot = format_ndot(satellite_dict["MEAN_MOTION_DOT"])
    nddot = format_sci(satellite_dict["MEAN_MOTION_DDOT"])
    bstar = format_sci(satellite_dict["BSTAR"])
    eph = satellite_dict["EPHEMERIS_TYPE"]
    elset = satellite_dict["ELEMENT_SET_NO"]

    line1_base = (
        f"1 {cat:05d}{clas} {obj_id} {epoch} {ndot} {nddot} {bstar} {eph} {elset: >4d}"
    )
    line1 = line1_base + calc_checksum(line1_base)

    # --- Build line 2 ---
    inc_str = format_float_str(satellite_dict["INCLINATION"], 8, 4)
    raan_str = format_float_str(satellite_dict["RA_OF_ASC_NODE"], 8, 4)
    ecc = format_eccentricity(satellite_dict["ECCENTRICITY"])
    argp_str = format_float_str(satellite_dict["ARG_OF_PERICENTER"], 8, 4)
    ma_str = format_float_str(satellite_dict["MEAN_ANOMALY"], 8, 4)
    mm_str = format_float_str(satellite_dict["MEAN_MOTION"], 11, 8)
    # Garante que a revolução não ultrapasse as 5 colunas estritas do TLE
    rev = satellite_dict["REV_AT_EPOCH"] % 100000

    line2_base = (
        f"2 {cat:05d} {inc_str} {raan_str} {ecc} {argp_str} {ma_str} {mm_str}{rev:5d}"
    )
    line2 = line2_base + calc_checksum(line2_base)

    return {"name": satellite_dict["OBJECT_NAME"], "line1": line1, "line2": line2}
