from logger import logger
from sys import exit
from sqlalchemy import create_engine, select, text, insert, update, bindparam
from config import settings
from pandas import to_datetime
from geopandas import GeoDataFrame, points_from_xy
from models import Base, Satellites
from utils import (
    celestrak_active_sat_tle_file,
    celestrak_active_sat_json_file,
    get_satellite_lat_lng,
)


def load_data(db_conn):
    df_celestrak_tle = celestrak_active_sat_tle_file()

    logger.log_info(
        f"Today's Celestrak Satellite TLE data downloaded! {len(df_celestrak_tle)} satellites found!"
    )

    df_celestrak_json = celestrak_active_sat_json_file()

    logger.log_info(
        f"Today's Celestrak Satellite JSON Metadata Downloaded! {len(df_celestrak_json)} satellites found!"
    )

    df_celestrak_json.rename(
        columns={
            "OBJECT_NAME": "name",
            "OBJECT_ID": "cospar_id",
            "NORAD_CAT_ID": "norad_id",
            "EPOCH": "epoch",
            "MEAN_MOTION": "mean_motion",
            "ECCENTRICITY": "eccentricity",
            "INCLINATION": "inclination",
            "RA_OF_ASC_NODE": "ra_of_asc_node",
            "ARG_OF_PERICENTER": "arg_of_pericenter",
            "MEAN_ANOMALY": "mean_anomaly",
            "EPHEMERIS_TYPE": "ephemeris_type",
            "CLASSIFICATION_TYPE": "classification_type",
            "ELEMENT_SET_NO": "element_set_no",
            "REV_AT_EPOCH": "rev_at_epoch",
            "BSTAR": "bstar",
            "MEAN_MOTION_DOT": "mean_motion_dot",
            "MEAN_MOTION_DDOT": "mean_motion_ddot",
        },
        inplace=True,
    )

    df_celestrak_json.epoch = to_datetime(df_celestrak_json.epoch)

    logger.log_info("Merging TLE data with JSON data...")

    df_newest_celestrak_data = df_celestrak_tle.merge(
        df_celestrak_json, how="inner", on="name"
    )

    logger.log_info(
        f"Merging complete! merge table created with {len(df_newest_celestrak_data)} rows!"
    )

    logger.log_info("Processing geographic data...")

    df_newest_celestrak_data["lat"] = 0.0
    df_newest_celestrak_data["lng"] = 0.0

    for index, row in df_newest_celestrak_data.iterrows():
        position = get_satellite_lat_lng(row.line1, row.line2, row["name"], row.epoch)
        df_newest_celestrak_data.loc[index, "lat"] = position["lat"]
        df_newest_celestrak_data.loc[index, "lng"] = position["lng"]

    gdf_newest_celestrak_data = GeoDataFrame(
        data=df_newest_celestrak_data,
        geometry=points_from_xy(
            df_newest_celestrak_data.lng, df_newest_celestrak_data.lat
        ),
        crs=4326,
    )

    logger.log_info("Checking if table has any data...")

    table_data = db_conn.execute(select(Satellites).limit(1)).all()

    table_has_data = len(table_data) > 0

    if not table_has_data:
        gdf_newest_celestrak_data.rename(columns={"geometry": "geom"}, inplace=True)
        logger.log_info("Table is empty, loading all satellites data into database!")
        db_conn.execute(
            insert(Satellites), gdf_newest_celestrak_data.to_wkt().to_dict("records")
        )
        db_conn.commit()
        logger.log_info(f"Satellites data inserted into database successfully!")
        return

    logger.log_info("Table has data, updating table...")

    try:
        gdf_newest_celestrak_data.rename(
            columns={"norad_id": "to_norad_id", "geometry": "geom"}, inplace=True
        )
        affected_rows = db_conn.execute(
            update(Satellites).where(Satellites.norad_id == bindparam("to_norad_id")),
            gdf_newest_celestrak_data.to_wkt().to_dict("records"),
        )
        db_conn.commit()
        logger.log_info(
            f"Table updated successfully! {affected_rows.rowcount} rows affected"
        )
    except BaseException as err:
        logger.log_error(f"Error updating!. Error msg: {err}")


if __name__ == "__main__":
    logger.initialize(
        name="celestrak_scrapper_logger",
        path=settings.logging.path,
        filename=settings.logging.filename,
    )
    logger.log_info("Starting script...")

    db_engine = create_engine(
        f"postgresql+psycopg2://{settings.postgis_user}:{settings.postgis_password}@{settings.database.host}:{settings.database.port}/{settings.database.name}"
    )

    try:
        db_engine.connect().execute(text("SELECT 1")).fetchone()
        logger.log_info("Database connection OK!")
    except BaseException as db_err:
        logger.log_error(
            f"Database connection error! Check configs or db connection!. Msg: {db_err}"
        )
        exit(1)

    with db_engine.connect() as conn:
        logger.log_info(
            f"Checking if table {settings.database.schema}.satellites exists..."
        )
        table_satellites_exists = conn.execute(
            text(
                f"SELECT * FROM pg_tables WHERE schemaname = '{settings.database.schema}' AND tablename = 'satellites'"
            )
        ).fetchone()

        if table_satellites_exists:
            logger.log_info("Table satellites exists!")
            logger.log_info("Starting to Collect and Load some satellites!")
            logger.start_timer("load_data_timer")
            load_data(conn)
            logger.log_info(
                f'Load data finished! Time elapsed: {logger.end_timer("load_data_timer")}h'
            )
        else:
            Base.metadata.create_all(db_engine)
            logger.log_warning("Table not found, MIGRATING... Execute script again!")
