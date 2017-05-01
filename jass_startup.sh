#!/usr/bin/env bash

# Used to start up jass from docker using gunicorn
python create_db_if_not_exist.py
gunicorn -w 4 -preload -b 0.0.0.0:5000 jass.simple_rest:APP --log-config=logging.conf
