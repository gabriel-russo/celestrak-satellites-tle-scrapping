// Copyright (C) 2026 Gabriel Russo
// See end of file for extended copyright information.

#include "postgres.h"
#include "datatype/timestamp.h"
#include "utils/timestamp.h"
#include "fmgr.h"
#include "utils/builtins.h"
#include "TLE.h"
#include "catalog/pg_type.h"

/*
 * SGP4_satellite_geographic_position computes the geographic position of a satellite
 * in the WGS84 reference system from a Two-Line Element set (TLE) and a given
 * timestamp, returning the result as a WKT string in the form "POINT Z(lon lat alt)".
 * The SQL signature of the function is:
 *
 *     satellite_geographic_position(
 *         line1   varchar,
 *         line2   varchar,
 *         at      timestamp
 *     ) RETURNS text
 *
 * The parameters line1 and line2 correspond to the standard NORAD TLE lines, and
 * the timestamp parameter represents the propagation instant. The timestamp is
 * expected to be expressed in UTC, since no time zone conversion is performed.
 * Internally, the function converts the PostgreSQL Timestamp value into a
 * struct pg_tm using timestamp2tm(), formats it as an ISO 8601 string
 * (YYYY-MM-DDTHH:MI:SS.US), and passes it to satellite_geographic_position().
 * That routine parses the TLE, propagates the orbit using the SGP4 algorithm,
 * converts the resulting TEME coordinates to ECEF using sidereal time, and
 * finally converts ECEF coordinates to geodetic latitude, longitude, and
 * altitude on the WGS84 ellipsoid. The resulting longitude (X), latitude (Y),
 * and altitude (Z) are formatted into a WKT POINT Z string and returned as text.
 * The altitude value is expressed in kilometers. The function is declared STRICT,
 * assumes valid TLE input, and does not depend on PostGIS headers or internal
 * geometry structures; spatial objects can be constructed on the SQL side using
 * ST_GeomFromText and ST_SetSRID with SRID 4326.
 */

PG_MODULE_MAGIC;

PG_FUNCTION_INFO_V1(SGP4_satellite_geographic_position);
Datum SGP4_satellite_geographic_position(PG_FUNCTION_ARGS)
{
    text *line1_text = PG_GETARG_TEXT_PP(0);
    text *line2_text = PG_GETARG_TEXT_PP(1);
    Timestamp ts = PG_GETARG_TIMESTAMP(2);

    char *line1 = text_to_cstring(line1_text);
    char *line2 = text_to_cstring(line2_text);

    /* timestamp -> ISO string */
    struct pg_tm tm;
    fsec_t fsec;

    if (timestamp2tm(ts, NULL, &tm, &fsec, NULL, NULL) != 0)
        ereport(ERROR, (errmsg("timestamp conversion failed")));

    char at[64];

    snprintf(at, sizeof(at),
             "%04d-%02d-%02dT%02d:%02d:%02d.%06d",
             tm.tm_year,
             tm.tm_mon,
             tm.tm_mday,
             tm.tm_hour,
             tm.tm_min,
             tm.tm_sec,
             (int)fsec);

    Position pos = satellite_geographic_position(line1, line2, at);

    char wkt[128];

    snprintf(wkt, sizeof(wkt),
             "POINT Z(%.10f %.10f %.6f)",
             pos.longitude,
             pos.latitude,
             pos.altitude);

    PG_RETURN_TEXT_P(cstring_to_text(wkt));
}

// MIT License
//
// Copyright (C) 2026 Gabriel Russo
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
