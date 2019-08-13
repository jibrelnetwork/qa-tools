#!/bin/bash -e

pip3 download --no-cache-dir -r /app/requirements.txt -d /srv/pypi
export PYTHONPATH=/app
cd /app
python3 setup.py sdist bdist_wheel -d /srv/pypi
