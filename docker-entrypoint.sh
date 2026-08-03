#!/bin/sh
set -e

mkdir -p /app/data
chown -R bot:bot /app/data

exec gosu bot "$@"
