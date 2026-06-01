--
-- NEEDS SGP4 EXTENSION TO WORK - https://github.com/gabriel-russo/postgresql-sgp4
--

CREATE VIEW celestrak.vw_satellites_now AS (
	SELECT
		norad_id AS norad_id,
		name AS name,
		NOW() AS local_time,
		NOW() AT TIME ZONE 'UTC' AS utc_time,
		celestrak.satellite_geographic_position_2d(line1, line2, NOW() AT TIME ZONE 'UTC') as geom
	FROM celestrak.satellites
);

CREATE OR REPLACE FUNCTION celestrak.satellite_geographic_position(
    LINE1 CHARACTER VARYING,
    LINE2 CHARACTER VARYING,
    AT_DATETIME TIMESTAMP WITHOUT TIME ZONE
) RETURNS GEOMETRY (POINTZ, 4326)
LANGUAGE PLPGSQL
AS $$
BEGIN
    RETURN ST_SetSRID(
        ST_GeomFromText(
            SATELLITE_GEOGRAPHIC_POSITION(
                LINE1,
                LINE2,
                AT_DATETIME
            )
        ), 4326
    );
END
$$;

CREATE OR REPLACE FUNCTION celestrak.satellite_geographic_position_2d(
    LINE1 CHARACTER VARYING,
    LINE2 CHARACTER VARYING,
    AT_DATETIME TIMESTAMP WITHOUT TIME ZONE
) RETURNS GEOMETRY (POINT, 4326)
LANGUAGE PLPGSQL
AS $$
BEGIN
    RETURN ST_SetSRID(
        ST_Force2D(
            ST_GeomFromText(
                SATELLITE_GEOGRAPHIC_POSITION(
                    LINE1,
                    LINE2,
                    AT_DATETIME
                )
            )
        ), 4326);
END
$$;

CREATE OR REPLACE FUNCTION celestrak.satellite_route_prediction(
    LINE1 CHARACTER VARYING,
    LINE2 CHARACTER VARYING,
    START_DATETIME TIMESTAMP WITHOUT TIME ZONE,
	STEP_MINUTES INTEGER,
	MAXIMUM_MINUTES INTEGER
) RETURNS GEOMETRY (LINESTRING, 4326)
LANGUAGE PLPGSQL
AS $$
DECLARE
	vertix GEOMETRY(POINT, 4326)[];
BEGIN
	FOR num IN 1..MAXIMUM_MINUTES BY STEP_MINUTES LOOP
		vertix := ARRAY_APPEND(vertix, celestrak.satellite_geographic_position_2d(LINE1, LINE2, START_DATETIME + make_interval(mins => num)));
	END LOOP;
	RETURN ST_MakeLine(vertix);
END
$$;
