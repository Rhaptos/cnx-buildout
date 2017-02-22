#!/bin/bash
# We're discarding the rest of the params that are sent
unset PYTHONPATH
/usr/bin/unoconv --stdout --format=odt "$1"
