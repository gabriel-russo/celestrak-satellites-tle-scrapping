from logger import logger
from sys import exit
from datetime import timedelta
from sqlalchemy import create_engine, text, select
from sqlalchemy.sql.functions import now
from sqlalchemy.dialects.postgresql import insert
from config import settings
from pandas import to_datetime
from geopandas import GeoDataFrame
from models import Base, Satellites
from utils import (
    celestrak_active_sat_tle_file,
    celestrak_active_sat_json_file,
    get_satellite_lat_lng,
    create_linestring_from_points,
    create_point,
)


def scrap_data(db_conn):
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

    logger.log_info("Processing geospatial data...")

    df_newest_celestrak_data["geom"] = None

    for index, row in df_newest_celestrak_data.iterrows():
        forecast_position_points = []

        for hour in range(0, 13):
            position_forecast = get_satellite_lat_lng(
                row.line1,
                row.line2,
                row["name"],
                row.epoch + timedelta(hours=hour),
            )
            forecast_position_points.append(create_point(**position_forecast))

        df_newest_celestrak_data.loc[index, "geom"] = create_linestring_from_points(
            forecast_position_points.copy()
        )

        forecast_position_points.clear()

    gdf_newest_celestrak_data = GeoDataFrame(
        data=df_newest_celestrak_data,
        geometry="geom",
        crs=4326,
    )

    logger.log_info("Inserting data into database...")

    for index, row in gdf_newest_celestrak_data.to_wkt().iterrows():
        stmt = insert(Satellites).values(row.to_dict())

        stmt = stmt.on_conflict_do_update(
            index_elements=["norad_id"],
            set_={
                "line1": stmt.excluded.line1,
                "line2": stmt.excluded.line2,
                "epoch": stmt.excluded.epoch,
                "mean_motion": stmt.excluded.mean_motion,
                "eccentricity": stmt.excluded.eccentricity,
                "inclination": stmt.excluded.inclination,
                "ra_of_asc_node": stmt.excluded.ra_of_asc_node,
                "arg_of_pericenter": stmt.excluded.arg_of_pericenter,
                "mean_anomaly": stmt.excluded.mean_anomaly,
                "ephemeris_type": stmt.excluded.ephemeris_type,
                "classification_type": stmt.excluded.classification_type,
                "element_set_no": stmt.excluded.element_set_no,
                "rev_at_epoch": stmt.excluded.rev_at_epoch,
                "bstar": stmt.excluded.bstar,
                "mean_motion_dot": stmt.excluded.mean_motion_dot,
                "mean_motion_ddot": stmt.excluded.mean_motion_ddot,
                "last_change": now(),
            },
            where=text(
                "EXCLUDED.fingerprint <> satellites.fingerprint AND EXCLUDED.epoch > satellites.epoch"
            ),
        )

        result = db_conn.execute(stmt)

        logger.do_count("insert", result.rowcount)

    db_conn.commit()

    logger.log_info(f"Satellites data inserted into database successfully!")


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
        db_engine.connect().execute(select(1)).fetchone()
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
            logger.log_info("Table OK... Starting to Collect some satellite data!")
            logger.start_timer("load_data_timer")
            scrap_data(conn)
            logger.log_info("Load data finished!")
            logger.log_info(f'{logger.get_count("insert")} inserted or updated rows!')
            logger.log_info(f'Time elapsed: {logger.end_timer("load_data_timer")}h')
        else:
            Base.metadata.create_all(db_engine)
            logger.log_warning("Table not found, MIGRATING... Execute script again!")
