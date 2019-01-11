#!/usr/bin/env bash
set -Eeuo pipefail

# This file is modeled from https://github.com/docker-library/postgres/blob/3f585c58df93e93b730c09a13e8904b96fa20c58/docker-entrypoint.sh

# Configure files
confd -onetime -backend env

# Rerun buildout for configuration
# TODO: run a specific recipe instead of everything
# -vvv :: very very verbose
# -o :: off-line mode
# -c file :: specify a config file
echo "Running buildout to reconfigure hostnames... just a sec"
bin/buildout -vvv -o -c docker-buildout.cfg install >> buildout.log 2>&1

# Run the given command
echo "$@"
exec "$@"
