CREATE OR REPLACE FUNCTION CELESTRAK.GEOGRAPHIC_POSITION_OF (
    LINE1 CHARACTER VARYING,
    LINE2 CHARACTER VARYING,
    AT_DATETIME TIMESTAMP WITH TIME ZONE
) RETURNS GEOMETRY (POINTZ, 4326)
LANGUAGE PLPGSQL
AS $$
DECLARE
    ----------------------------------------------------------------------
    -- Physical constants
    ----------------------------------------------------------------------
    mu        CONSTANT DOUBLE PRECISION := 398600.4418;      -- km^3/s^2
    r_earth   CONSTANT DOUBLE PRECISION := 6378.137;         -- km (WGS84)
    j2        CONSTANT DOUBLE PRECISION := 1.08262668e-3;
    two_pi    CONSTANT DOUBLE PRECISION := 2.0 * pi();

    ----------------------------------------------------------------------
    -- WGS84 ellipsoid constants
    ----------------------------------------------------------------------
    f         CONSTANT DOUBLE PRECISION := 1.0 / 298.257223563;
    e2        CONSTANT DOUBLE PRECISION := f * (2.0 - f);

    ----------------------------------------------------------------------
    -- Parsed TLE elements
    ----------------------------------------------------------------------
    epoch_year        INTEGER;
    epoch_day         DOUBLE PRECISION;
    epoch_timestamp   TIMESTAMP WITH TIME ZONE;

    inclination_deg   DOUBLE PRECISION;
    raan_deg          DOUBLE PRECISION;
    eccentricity      DOUBLE PRECISION;
    argp_deg          DOUBLE PRECISION;
    mean_anomaly_deg  DOUBLE PRECISION;
    mean_motion_rev   DOUBLE PRECISION;

    ----------------------------------------------------------------------
    -- Orbital variables
    ----------------------------------------------------------------------
    dt                DOUBLE PRECISION;
    n0                DOUBLE PRECISION;   -- mean motion (rad/s)
    a                 DOUBLE PRECISION;   -- semi-major axis (km)

    i_rad             DOUBLE PRECISION;
    raan_rad          DOUBLE PRECISION;
    argp_rad          DOUBLE PRECISION;
    M0_rad            DOUBLE PRECISION;

    -- J2 secular rates
    p                 DOUBLE PRECISION;
    raan_dot          DOUBLE PRECISION;
    argp_dot          DOUBLE PRECISION;
    mean_motion_corr  DOUBLE PRECISION;

    -- Propagated elements
    raan_t            DOUBLE PRECISION;
    argp_t            DOUBLE PRECISION;
    M                 DOUBLE PRECISION;

    -- Kepler solution
    E                 DOUBLE PRECISION;
    nu                DOUBLE PRECISION;
    r_orb             DOUBLE PRECISION;

    -- Orbital plane coordinates
    x_orb             DOUBLE PRECISION;
    y_orb             DOUBLE PRECISION;

    -- ECI coordinates
    x_eci             DOUBLE PRECISION;
    y_eci             DOUBLE PRECISION;
    z_eci             DOUBLE PRECISION;

    ----------------------------------------------------------------------
    -- Earth rotation (GMST)
    ----------------------------------------------------------------------
    jd                DOUBLE PRECISION;
    T                 DOUBLE PRECISION;
    gmst_deg          DOUBLE PRECISION;
    gmst_rad          DOUBLE PRECISION;

    x_ecef            DOUBLE PRECISION;
    y_ecef            DOUBLE PRECISION;
    z_ecef            DOUBLE PRECISION;

    ----------------------------------------------------------------------
    -- Geodetic variables
    ----------------------------------------------------------------------
    lon               DOUBLE PRECISION;
    lat               DOUBLE PRECISION;
    h                 DOUBLE PRECISION;

    rho               DOUBLE PRECISION;
    N_curvature       DOUBLE PRECISION;

    lat_prev          DOUBLE PRECISION;
    iter              INTEGER;

BEGIN

    ----------------------------------------------------------------------
    -- Parse TLE epoch (UTC)
    ----------------------------------------------------------------------
    epoch_year := substring(LINE1 from 19 for 2)::INTEGER;
    epoch_day  := substring(LINE1 from 21 for 12)::DOUBLE PRECISION;

    IF epoch_year < 57 THEN
        epoch_year := epoch_year + 2000;
    ELSE
        epoch_year := epoch_year + 1900;
    END IF;

    epoch_timestamp :=
        make_timestamptz(epoch_year,1,1,0,0,0,'UTC')
        + ((epoch_day - 1.0) * interval '1 day');

    ----------------------------------------------------------------------
    -- Parse classical elements from TLE line 2
    ----------------------------------------------------------------------
    inclination_deg  := substring(LINE2 from 9  for 8)::DOUBLE PRECISION;
    raan_deg         := substring(LINE2 from 18 for 8)::DOUBLE PRECISION;
    eccentricity     := ('0.' || substring(LINE2 from 27 for 7))::DOUBLE PRECISION;
    argp_deg         := substring(LINE2 from 35 for 8)::DOUBLE PRECISION;
    mean_anomaly_deg := substring(LINE2 from 44 for 8)::DOUBLE PRECISION;
    mean_motion_rev  := substring(LINE2 from 53 for 11)::DOUBLE PRECISION;

    ----------------------------------------------------------------------
    -- Time since epoch (seconds)
    ----------------------------------------------------------------------
    dt := EXTRACT(EPOCH FROM (AT_DATETIME - epoch_timestamp));

    ----------------------------------------------------------------------
    -- Mean motion and semi-major axis
    ----------------------------------------------------------------------
    n0 := mean_motion_rev * two_pi / 86400.0;
    a  := power(mu / (n0*n0), 1.0/3.0);

    i_rad    := radians(inclination_deg);
    raan_rad := radians(raan_deg);
    argp_rad := radians(argp_deg);
    M0_rad   := radians(mean_anomaly_deg);

    ----------------------------------------------------------------------
    -- J2 secular perturbations
    ----------------------------------------------------------------------
    p := a * (1.0 - eccentricity*eccentricity);

    raan_dot :=
        -1.5 * j2 * (r_earth*r_earth) * sqrt(mu)
        / (power(p,2.0) * power(a,1.5))
        * cos(i_rad);

    argp_dot :=
         0.75 * j2 * (r_earth*r_earth) * sqrt(mu)
        / (power(p,2.0) * power(a,1.5))
        * (5.0*cos(i_rad)*cos(i_rad) - 1.0);

    mean_motion_corr :=
        n0 + 0.75 * j2 * (r_earth*r_earth) * sqrt(mu)
        / (power(p,2.0) * power(a,1.5))
        * sqrt(1.0 - eccentricity*eccentricity)
        * (3.0*cos(i_rad)*cos(i_rad) - 1.0);

    raan_t := raan_rad + raan_dot * dt;
    argp_t := argp_rad + argp_dot * dt;
    M      := M0_rad + mean_motion_corr * dt;

    M := M - two_pi * floor(M / two_pi);
    IF M < 0.0 THEN
        M := M + two_pi;
    END IF;

    ----------------------------------------------------------------------
    -- Solve Kepler equation (Newton-Raphson)
    ----------------------------------------------------------------------
    E := M;
    FOR iter IN 1..12 LOOP
        E := E - (E - eccentricity*sin(E) - M)
                / (1.0 - eccentricity*cos(E));
    END LOOP;

    nu := 2.0 * atan2(
        sqrt(1.0 + eccentricity) * sin(E/2.0),
        sqrt(1.0 - eccentricity) * cos(E/2.0)
    );

    r_orb := a * (1.0 - eccentricity*cos(E));

    ----------------------------------------------------------------------
    -- Orbital plane coordinates
    ----------------------------------------------------------------------
    x_orb := r_orb * cos(nu);
    y_orb := r_orb * sin(nu);

    ----------------------------------------------------------------------
    -- Orbital plane to ECI
    ----------------------------------------------------------------------
    x_eci :=
        x_orb * (cos(raan_t)*cos(argp_t) -
                 sin(raan_t)*sin(argp_t)*cos(i_rad))
      - y_orb * (cos(raan_t)*sin(argp_t) +
                 sin(raan_t)*cos(argp_t)*cos(i_rad));

    y_eci :=
        x_orb * (sin(raan_t)*cos(argp_t) +
                 cos(raan_t)*sin(argp_t)*cos(i_rad))
      - y_orb * (sin(raan_t)*sin(argp_t) -
                 cos(raan_t)*cos(argp_t)*cos(i_rad));

    z_eci :=
        x_orb * (sin(argp_t)*sin(i_rad)) +
        y_orb * (cos(argp_t)*sin(i_rad));

    ----------------------------------------------------------------------
    -- Julian Date and GMST
    ----------------------------------------------------------------------
    jd := 2440587.5 + EXTRACT(EPOCH FROM AT_DATETIME) / 86400.0;
    T  := (jd - 2451545.0) / 36525.0;

    gmst_deg :=
        280.46061837
        + 360.98564736629 * (jd - 2451545.0)
        + 0.000387933 * T*T
        - (T*T*T) / 38710000.0;

    gmst_deg := gmst_deg - 360.0 * floor(gmst_deg / 360.0);
    gmst_rad := radians(gmst_deg);

    ----------------------------------------------------------------------
    -- ECI to ECEF
    ----------------------------------------------------------------------
    x_ecef :=  x_eci * cos(gmst_rad) + y_eci * sin(gmst_rad);
    y_ecef := -x_eci * sin(gmst_rad) + y_eci * cos(gmst_rad);
    z_ecef :=  z_eci;

    ----------------------------------------------------------------------
    -- ECEF to WGS84 geodetic (iterative solution)
    ----------------------------------------------------------------------
    lon := atan2(y_ecef, x_ecef);

    rho := sqrt(x_ecef*x_ecef + y_ecef*y_ecef);
    lat := atan2(z_ecef, rho * (1.0 - e2));

    FOR iter IN 1..6 LOOP
        lat_prev := lat;
        N_curvature := r_earth / sqrt(1.0 - e2 * sin(lat)*sin(lat));
        lat := atan2(z_ecef + e2*N_curvature*sin(lat), rho);
        EXIT WHEN abs(lat - lat_prev) < 1e-12;
    END LOOP;

    N_curvature := r_earth / sqrt(1.0 - e2 * sin(lat)*sin(lat));
    h := rho / cos(lat) - N_curvature;

    ----------------------------------------------------------------------
    -- Return geographic PointZ (meters)
    ----------------------------------------------------------------------
    RETURN ST_SetSRID(
        ST_MakePoint(degrees(lon), degrees(lat), h * 1000.0),
        4326
    );

END;
$$;

-- This function implements an orbital propagator based on TLE elements using a
-- Keplerian two-body model enhanced with secular J2 perturbations. It parses
-- the epoch and classical orbital elements from the two TLE lines, converts the
-- mean motion to radians per second, and computes the semi-major axis using
-- Kepler’s third law. The orbit is propagated forward in time from the TLE epoch
-- using corrected secular rates for the right ascension of the ascending node
-- (RAAN), argument of perigee, and mean anomaly derived from the J2 oblateness
-- effect of the Earth. Kepler’s equation is solved numerically using the
-- Newton-Raphson method to obtain the eccentric anomaly, which is then converted
-- to true anomaly and orbital radius. The position is computed in the orbital
-- plane and transformed to Earth-Centered Inertial (ECI) coordinates using the
-- updated orbital elements. The function calculates the Julian Date from the
-- provided timestamp with time zone and evaluates Greenwich Mean Sidereal Time
-- (GMST) to rotate the inertial coordinates into Earth-Centered Earth-Fixed
-- (ECEF) coordinates. Finally, it converts ECEF coordinates into geodetic
-- latitude, longitude, and altitude using an iterative WGS84 ellipsoidal model,
-- returning a 3D geographic point (longitude, latitude, altitude in meters).
--
-- Although this implementation significantly improves accuracy compared to a
-- pure Keplerian model by including J2 secular effects and a proper WGS84
-- geodetic conversion, it is not a complete SGP4 implementation. It does not
-- use the TEME reference frame, does not apply the full set of secular and
-- periodic corrections defined in the SGP4 theory, does not model atmospheric
-- drag through the BSTAR parameter, and does not implement the deep-space
-- branch (SDP4) required for high-altitude orbits. It also does not perform
-- the full TEME-to-ITRF transformation pipeline or handle UT1-based Earth
-- orientation parameters. Therefore, this function should be considered an
-- enhanced analytical propagator with J2 corrections rather than a fully
-- NORAD-compliant SGP4 implementation.
--
-- Distance, in degrees, between SGP4 generated point vs. The function above generated point.
-- at_datetime = epoch
--
-- "avg"	"stddev"	"variance"	"max"	 "min"
-- 0.4427	0.6589	     0.4342	    31.3832	 0.0040
