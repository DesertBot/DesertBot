#!/bin/bash
set -e

# create dummy APIKeys.json file if none exists
if [ ! -f APIKeys.json ]; then
    echo "{}" > APIKeys.json
fi

# ensure images are up to date
docker compose build

# run comics test
docker compose run --rm comics

# run desertbot tests
docker compose run --rm desertbot
