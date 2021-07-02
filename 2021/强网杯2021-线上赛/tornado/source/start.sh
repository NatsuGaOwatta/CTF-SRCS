#!/bin/bash
chown -R mysql:mysql /var/lib/mysql
service mysql restart
su - mysql /bin/sh -c "python3 /qwb/app/app.py"