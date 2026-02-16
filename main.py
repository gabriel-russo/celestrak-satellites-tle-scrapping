from psycopg import connect
from psycopg.connection import Connection
from celestrak import celestrak_active_satellites
from config import read_config
from logger import Logger
from utils import create_point, get_satellite_lat_lng

log = Logger(tag="celestrak")


def main(conn: Connection):
    with conn.cursor() as cur:
        for satellite in celestrak_active_satellites():

            geom = create_point(
                **get_satellite_lat_lng(
                    satellite["line1"], satellite["line2"], satellite["epoch"]
                )
            )

            log.debug(
                f"Inserting {satellite['name']} - X {geom.x} Y {geom.y} Z {geom.z}"
            )

            cur.execute(
                """
            INSERT INTO celestrak.satellites (
            norad_id,
            cospar_id,
            name,
            line1,
            line2,
            epoch,
            mean_motion,
            eccentricity,
            inclination,
            ra_of_asc_node,
            arg_of_pericenter,
            mean_anomaly,
            ephemeris_type,
            classification_type,
            element_set_no,
            rev_at_epoch,
            bstar,
            mean_motion_dot,
            mean_motion_ddot,
            geom
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT satellite_identity DO UPDATE
            SET
            cospar_id = EXCLUDED.cospar_id,
            name = EXCLUDED.name,
            line1 = EXCLUDED.line1,
            line2 = EXCLUDED.line2,
            epoch = EXCLUDED.epoch,
            mean_motion = EXCLUDED.mean_motion,
            eccentricity = EXCLUDED.eccentricity,
            inclination = EXCLUDED.inclination,
            ra_of_asc_node = EXCLUDED.ra_of_asc_node,
            arg_of_pericenter = EXCLUDED.arg_of_pericenter,
            mean_anomaly = EXCLUDED.mean_anomaly,
            ephemeris_type = EXCLUDED.ephemeris_type,
            classification_type = EXCLUDED.classification_type,
            element_set_no = EXCLUDED.element_set_no,
            rev_at_epoch = EXCLUDED.rev_at_epoch,
            bstar = EXCLUDED.bstar,
            mean_motion_dot = EXCLUDED.mean_motion_dot,
            mean_motion_ddot = EXCLUDED.mean_motion_ddot,
            geom = EXCLUDED.geom
            """,
                (
                    satellite["norad_id"],
                    satellite["cospar_id"],
                    satellite["name"],
                    satellite["line1"],
                    satellite["line2"],
                    satellite["epoch"],
                    satellite["mean_motion"],
                    satellite["eccentricity"],
                    satellite["inclination"],
                    satellite["ra_of_asc_node"],
                    satellite["arg_of_pericenter"],
                    satellite["mean_anomaly"],
                    satellite["ephemeris_type"],
                    satellite["classification_type"],
                    satellite["element_set_no"],
                    satellite["rev_at_epoch"],
                    satellite["bstar"],
                    satellite["mean_motion_dot"],
                    satellite["mean_motion_ddot"],
                    geom.wkt,
                ),
            )


def start():
    config = read_config()

    if config.DEBUG:
        log.enable_debug_mode()

    conn = connect(
        f"host={config.HOST} "
        f"port={config.PORT} "
        f"dbname={config.NAME} "
        f"user={config.DB_USER} "
        f"password={config.DB_PASSWORD} "
        "application_name=celestrak_scrapper"
    )

    with conn:
        main(conn=conn)


if __name__ == "__main__":
    log.info("Initializing script.")
    start()
    log.info("Script finished.")
