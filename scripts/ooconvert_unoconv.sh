#!/bin/bash
# We're discarding the rest of the params that are sent
python3 /usr/local/bin/unoconv --stdout --format=odt "$1"
