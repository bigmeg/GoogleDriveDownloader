#!/bin/sh
PORT=$(awk -F "=" '/SERVER_PORT/ {print $2}' settings.ini | xargs)
docker run  -d -p $PORT:$PORT -v ~/Downloads/:/root/Downloads --restart unless-stopped gdd
