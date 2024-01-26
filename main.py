from pandas import DataFrame
from sqlalchemy import create_engine, select, text, insert, update, bindparam
from config import settings
from logger import Logger
from models import Base, Satellites
from utils import (
    remove_whitespace,
    celestrak_active_sat_tle_file,
    celestrak_active_sat_json_file,
)


def update_data(engine):
    logger = Logger()

    df_current_celestrak_data = celestrak_active_sat_tle_file()

    logger.log("UPDATE | Checking for outdated satellites data")

    with engine.connect() as conn:
        db_rows = conn.execute(
            select(Satellites.name, Satellites.line1, Satellites.line2)
        ).all()

        df_current_db_data = DataFrame(db_rows, columns=["name", "line1", "line2"])

        # Remove whitespace to more precise comparison
        df_current_db_cleaned = df_current_db_data[["line1", "line2"]].map(
            remove_whitespace
        )

        df_current_celestrak_cleaned = df_current_celestrak_data[
            ["line1", "line2"]
        ].map(remove_whitespace)

        diff = df_current_celestrak_data[
            ~df_current_celestrak_cleaned.line1.isin(df_current_db_cleaned.line1)
            | ~df_current_celestrak_cleaned.line2.isin(df_current_db_cleaned.line2)
        ].copy()

        diff.rename(columns={"name": "u_name"}, inplace=True)

        diff.dropna(inplace=True)

        if not diff.empty:
            logger.log(
                f"UPDATE | {len(diff)} diff data - Updating satellites data (not cleaned)"
            )

            affected_rows = conn.execute(
                update(Satellites).where(Satellites.name == bindparam("u_name")),
                diff.to_dict("records"),
            )

            conn.commit()

            logger.log(
                f"UPDATE | Satellites Updated Successfully! {affected_rows.rowcount} rows affected"
            )
        else:
            logger.log("UPDATE | No satellites to update")


def search_new_data(engine):
    logger = Logger()

    df_current_celestrak_data = celestrak_active_sat_tle_file()

    logger.log("NEW | Checking for new satellites")

    with engine.connect() as conn:
        db_rows = conn.execute(
            select(Satellites.name, Satellites.line1, Satellites.line2)
        ).all()

        df_current_db_data = DataFrame(db_rows, columns=["name", "line1", "line2"])

        df_new_satellites = df_current_celestrak_data[
            ~df_current_celestrak_data.name.isin(df_current_db_data.name)
        ].copy()

        df_new_satellites.dropna(inplace=True)

        if not df_new_satellites.empty:
            logger.log(
                f"NEW | New {len(df_new_satellites)} satellites detected! (Not cleaned)"
            )

            df_celestrak_json = celestrak_active_sat_json_file()[
                ["OBJECT_NAME", "NORAD_CAT_ID", "OBJECT_ID"]
            ].copy()

            df_celestrak_json.rename(
                columns={
                    "OBJECT_NAME": "name",
                    "OBJECT_ID": "cospar_id",
                    "NORAD_CAT_ID": "norad_id",
                },
                inplace=True,
            )

            df_new_satellites_ids = df_celestrak_json[
                df_celestrak_json.name.isin(df_new_satellites.name)
            ].copy()

            if not df_new_satellites_ids.empty:
                new_satellites_full_data = df_new_satellites.merge(
                    df_new_satellites_ids, on="name"
                )

                new_satellites_full_data.dropna(inplace=True)

                conn.execute(
                    insert(Satellites), new_satellites_full_data.to_dict("records")
                )

                conn.commit()

                logger.log(
                    f"NEW | New {len(new_satellites_full_data)} satellites data inserted into database successfully! (Cleaned)"
                )
            else:
                logger.log("NEW | No new satellites found")
        else:
            logger.log("NEW | No new satellites found")


def load_data(engine):
    logger = Logger()

    celestrak_tle = celestrak_active_sat_tle_file()

    logger.log(
        f"LOAD | Celestrak Satellite data downloaded, {len(celestrak_tle)} satellites found"
    )

    celestrak_json = celestrak_active_sat_json_file()[
        ["OBJECT_NAME", "NORAD_CAT_ID", "OBJECT_ID"]
    ].copy()

    celestrak_json.rename(
        columns={
            "OBJECT_NAME": "name",
            "OBJECT_ID": "cospar_id",
            "NORAD_CAT_ID": "norad_id",
        },
        inplace=True,
    )

    full_celestrak_data = celestrak_tle.merge(
        celestrak_json, left_on="name", right_on="name"
    )

    with engine.connect() as conn:
        logger.log("LOAD | Inserting found satellites data into database")
        conn.execute(insert(Satellites), full_celestrak_data.to_dict("records"))
        conn.commit()
        logger.log("LOAD | Satellites data inserted into database successfully")


if __name__ == "__main__":
    db_engine = create_engine(
        f"postgresql+psycopg2://{settings.postgis_user}:{settings.postgis_password}@{settings.database.host}:{settings.database.port}/{settings.database.name}"
    )

    with db_engine.connect() as conn:
        table_satellites_exists = conn.execute(
            text(
                f"SELECT * FROM pg_tables WHERE schemaname = '{settings.database.schema}' AND tablename = 'satellites'"
            )
        ).fetchone()

        if table_satellites_exists:
            any_satellite_data = conn.execute(select(Satellites).limit(1)).fetchone()

            if any_satellite_data:
                update_data(db_engine)
                search_new_data(db_engine)
            else:
                load_data(db_engine)
        else:
            Base.metadata.create_all(db_engine)
            print("Table not found, MIGRATING...")
