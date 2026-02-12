EXTENSION = sgp4
MODULE_big = sgp4

OBJS = sgp4.o SGP4.o TLE.o

DATA = sgp4--0.1.sql

PG_CONFIG = pg_config
PGXS := $(shell $(PG_CONFIG) --pgxs)
include $(PGXS)
