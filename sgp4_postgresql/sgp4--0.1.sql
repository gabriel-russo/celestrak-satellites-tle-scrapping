CREATE FUNCTION satellite_geographic_position(
    line1 VARCHAR,
    line2 VARCHAR,
    at_datetime TIMESTAMP WITHOUT TIME ZONE
)
RETURNS TEXT
AS '$libdir/sgp4', 'SGP4_satellite_geographic_position'
LANGUAGE C STRICT IMMUTABLE;
