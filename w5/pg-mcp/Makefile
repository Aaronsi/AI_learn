# Simple Makefile to recreate test fixtures
# Requires: createdb, dropdb, psql available in PATH
# Uses standard PG* environment variables (PGHOST, PGUSER, PGPASSWORD, PGPORT)

DB_SMALL  ?= pg_mcp_small
DB_MEDIUM ?= pg_mcp_medium
DB_LARGE  ?= pg_mcp_large

PSQL ?= psql
CREATEDB ?= createdb
DROPDB ?= dropdb

.PHONY: all createdbs dropdbs load-small load-medium load-large load-all reset-small reset-medium reset-large reset-all

all: reset-all

createdbs:
	$(CREATEDB) $(DB_SMALL)
	$(CREATEDB) $(DB_MEDIUM)
	$(CREATEDB) $(DB_LARGE)

dropdbs:
	-$(DROPDB) $(DB_SMALL)
	-$(DROPDB) $(DB_MEDIUM)
	-$(DROPDB) $(DB_LARGE)

load-small:
	$(PSQL) -d $(DB_SMALL) -f fixtures/small.sql

load-medium:
	$(PSQL) -d $(DB_MEDIUM) -f fixtures/medium.sql

load-large:
	$(PSQL) -d $(DB_LARGE) -f fixtures/large.sql

load-all: load-small load-medium load-large

reset-small: dropdbs createdbs load-small

reset-medium: dropdbs createdbs load-medium

reset-large: dropdbs createdbs load-large

reset-all: dropdbs createdbs load-all

