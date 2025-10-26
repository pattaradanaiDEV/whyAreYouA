#!/bin/sh

# Use the classic docker-compose command with a hyphen, 
# which is compatible with the 'docker/compose:1.29.2' image.
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml --compatibility up -d