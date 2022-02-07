#!/bin/bash -e

# We need to ensure this directory is writeable on start of the container
chmod 0777 /var/lib/grafana

exec /usr/bin/supervisord

influx -execute "create database ouradb"
python3 /etc/oura/oura_post_to_influxdb.py `date +"%Y-%m-%d"`

