CREATE SCHEMA IF NOT EXISTS "celestrak";

CREATE TABLE IF NOT EXISTS celestrak.satellites (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    norad_id INTEGER NOT NULL,
    cospar_id VARCHAR(10),
    name VARCHAR(24) NOT NULL,
    line1 VARCHAR(128) NOT NULL,
    line2 VARCHAR(128) NOT NULL,
    epoch TIMESTAMP WITH TIME ZONE NOT NULL,
    mean_motion DOUBLE PRECISION,
    eccentricity DOUBLE PRECISION,
    inclination DOUBLE PRECISION,
    ra_of_asc_node DOUBLE PRECISION,
    arg_of_pericenter DOUBLE PRECISION,
    mean_anomaly DOUBLE PRECISION,
    ephemeris_type SMALLINT,
    classification_type VARCHAR(4),
    element_set_no SMALLINT,
    rev_at_epoch INTEGER,
    bstar DOUBLE PRECISION,
    mean_motion_dot DOUBLE PRECISION,
    mean_motion_ddot DOUBLE PRECISION,
    proc_time TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    geom GEOMETRY(PointZ, 4326) NOT NULL,
    geom2d GEOMETRY(Point, 4326) GENERATED ALWAYS AS (ST_Force2D(geom)) STORED,
    CONSTRAINT satellite_identity UNIQUE (norad_id)
);

COMMENT ON COLUMN celestrak.satellites.norad_id IS
'NORAD Catalog Number. Unique satellite identifier assigned by the U.S. Space Surveillance Network and used in the Two-Line Element (TLE) format.';

COMMENT ON COLUMN celestrak.satellites.cospar_id IS
'International Designator (COSPAR ID). Identifies the launch year, launch number of that year, and the piece of the launch (e.g., 1998-067A).';

COMMENT ON COLUMN celestrak.satellites.name IS
'Common name of the space object as published by CelesTrak or associated satellite catalogs.';

COMMENT ON COLUMN celestrak.satellites.line1 IS
'First line of the Two-Line Element (TLE) set, containing catalog number, classification, epoch, drag terms, ephemeris type, and element set number.';

COMMENT ON COLUMN celestrak.satellites.line2 IS
'Second line of the Two-Line Element (TLE) set, containing the classical orbital elements such as inclination, RAAN, eccentricity, argument of perigee, mean anomaly, and mean motion.';

COMMENT ON COLUMN celestrak.satellites.epoch IS
'Epoch time of the TLE expressed as a timestamp with time zone. Corresponds to the fractional day-of-year value encoded in line 1 of the TLE.';

COMMENT ON COLUMN celestrak.satellites.mean_motion IS
'Mean motion in revolutions per day, representing the average angular speed of the satellite around the Earth as defined in the TLE (line 2, columns 53-63).';

COMMENT ON COLUMN celestrak.satellites.eccentricity IS
'Orbital eccentricity from the TLE (line 2, columns 27-33). In the TLE format, it is stored without a leading decimal point.';

COMMENT ON COLUMN celestrak.satellites.inclination IS
'Orbital inclination in degrees relative to the Earth equatorial plane (line 2, columns 9-16).';

COMMENT ON COLUMN celestrak.satellites.ra_of_asc_node IS
'Right Ascension of the Ascending Node (RAAN) in degrees, measured in the Earth-centered inertial frame (line 2, columns 18-25).';

COMMENT ON COLUMN celestrak.satellites.arg_of_pericenter IS
'Argument of perigee in degrees, defining the orientation of the orbit within its orbital plane (line 2, columns 35-42).';

COMMENT ON COLUMN celestrak.satellites.mean_anomaly IS
'Mean anomaly in degrees at the epoch, indicating the satellite position along its orbit at the TLE epoch (line 2, columns 44-51).';

COMMENT ON COLUMN celestrak.satellites.ephemeris_type IS
'Ephemeris type indicator from line 1 of the TLE. For standard public TLEs, this value is typically 0 and corresponds to the SGP4/SDP4 orbital model.';

COMMENT ON COLUMN celestrak.satellites.classification_type IS
'Security classification of the object as indicated in line 1 of the TLE (e.g., U = Unclassified).';

COMMENT ON COLUMN celestrak.satellites.element_set_no IS
'Element set number from line 1 of the TLE, incremented each time a new TLE is generated for the object.';

COMMENT ON COLUMN celestrak.satellites.rev_at_epoch IS
'Revolution number at epoch from line 2 of the TLE, indicating the total number of orbits completed by the satellite at the epoch time.';

COMMENT ON COLUMN celestrak.satellites.bstar IS
'BSTAR drag term from line 1 of the TLE, representing a scaled atmospheric drag coefficient used internally by the SGP4 model.';

COMMENT ON COLUMN celestrak.satellites.mean_motion_dot IS
'First time derivative of the mean motion (rev/day^2), representing secular acceleration due to drag effects, as encoded in line 1 of the TLE.';

COMMENT ON COLUMN celestrak.satellites.mean_motion_ddot IS
'Second time derivative of the mean motion (rev/day^3), historically included in the TLE format but typically unused by the standard SGP4 implementation.';

CREATE INDEX index_satellites_name ON celestrak.satellites(name);

CREATE INDEX index_satellites_geom ON celestrak.satellites USING GIST(geom);

CREATE TABLE IF NOT EXISTS celestrak.satellites_log (
    norad_id INTEGER NOT NULL,
    name VARCHAR(24) NOT NULL,
    line1 VARCHAR(128) NOT NULL,
    line2 VARCHAR(128) NOT NULL,
    epoch TIMESTAMP WITH TIME ZONE NOT NULL,
    proc_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    geom GEOMETRY(PointZ, 4326) NOT NULL
);

CREATE OR REPLACE FUNCTION celestrak.trigger_fn_satellites_log() RETURNS TRIGGER
LANGUAGE PLPGSQL
AS $$
BEGIN
    INSERT INTO celestrak.satellites_log (norad_id, name, line1, line2, epoch, proc_time, geom)
    VALUES (OLD.norad_id, OLD.name, OLD.line1, OLD.line2, OLD.epoch, OLD.proc_time, OLD.geom);

    RETURN NULL;
END
$$;

CREATE OR REPLACE TRIGGER trigger_satellites_log
AFTER UPDATE ON celestrak.satellites
FOR EACH ROW
WHEN (OLD.line1 IS DISTINCT FROM NEW.line1 OR OLD.line2 IS DISTINCT FROM NEW.line2)
EXECUTE FUNCTION celestrak.trigger_fn_satellites_log();
