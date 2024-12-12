#!/bin/bash

sleep 3

python manage.py makemigrations
python manage.py migrate


exec supervisord -n
