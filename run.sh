#!/bin/sh
PORT=$(awk -F "=" '/SERVER_PORT/ {print $2}' settings.ini)
docker run -d -p $PORT:$PORT -v ~/Downloads/:/root/Downloads gdd