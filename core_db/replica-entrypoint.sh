#!/bin/sh
set -eu

if [ "$(id -u)" = "0" ]; then
  mkdir -p "$PGDATA"
  chown -R postgres:postgres "$(dirname "$PGDATA")"
  exec gosu postgres sh "$0"
fi

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  until pg_basebackup --host=core_db --username=replicator --pgdata="$PGDATA" --write-recovery-conf --wal-method=stream --progress; do
    echo "Waiting for primary database..."
    sleep 1
  done
fi

chmod 700 "$PGDATA"

exec postgres -c hot_standby=on
