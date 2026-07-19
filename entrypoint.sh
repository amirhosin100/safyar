#!/bin/bash

python manage.py migrate;
python manage.py collectstatic --noinput;
gunicorn config.wsgi:application -w 4 -b 0.0.0.0:8000 --access-logfile - ;

