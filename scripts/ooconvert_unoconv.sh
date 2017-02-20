#!/bin/bash
# We're discarding the rest of the params that are sent
"${BASH_SOURCE[0]%/*}/unoconv" --stdout "$1"
