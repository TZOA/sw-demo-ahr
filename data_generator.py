#!/usr/bin/env python3
# ### BEGIN INIT INFO
# Provides:          data_generator.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO

import psycopg2
from pprint import pprint
from time import time
from datetime import datetime
import threading
from math import sin, pi

data_source_context = {'host': 'localhost',
                       'dbname': 'pi',
                       'user': 'pi',
                       'password': 'pi'}

DEVICE_ID = 'D2000-00001'

conn = None


def connect_to_db():
    global conn

    if conn is not None:
        try:
            cur = conn.cursor()
            with cur:
                cur.execute("SELECT version()")

                #print(cur.fetchone()[0])
        except psycopg2.OperationalError:
            conn = None

    if conn is None:
        try:
            conn = psycopg2.connect(**data_source_context)
            print('Connected to database!')
        except psycopg2.OperationalError:
            conn = None

    if conn is None:
        print('Disconnected from database!')


def inject_data():
    global conn

    connect_to_db()

    if conn is None:
        return

    try:
        with conn:
            cur = conn.cursor()

            u = time()*2*pi

            temperature = sin(u / 3600)*3 + sin(u / (60*17))*0.2 + sin(u / (60*73))*0.8 + 18
            airflow     = sin(u / 3600)*3 + sin(u / (60*17))*0.2 + sin(u / (60*73))*0.8 + 18
            pressure    = sin(u / 7200)*100 + sin(u / (60*48))*5 + sin(u / (60*156))*20 + 1000
            humidity    = sin(u / 1900)*20 + sin(u / (60*44))*5 + sin(u / (60*277))*10 + 40
            voc         = sin(u / 3600)*3 + sin(u / (60*17))*0.2 + sin(u / (60*73))*0.8 + 18
            co2         = sin(u / 3600)*200 + sin(u / (60*66))*60 + sin(u / (60*149))*120 + 407
            pm25        = sin(u / 3600)*10 + sin(u / (60*23))*3 + sin(u / (60*56))*7 + 15

            print(u, temperature, airflow, pressure, humidity, voc, co2, pm25)

            with cur:
                cur.execute("INSERT INTO telemetry (device_id, timestamp, "
                            "temperature, airflow, pressure, humidity, voc, co2, pm25)"
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (DEVICE_ID, datetime.now(),
                             temperature, airflow, pressure, humidity, voc, co2, pm25))

    except psycopg2.OperationalError:
        conn = None

from subprocess import Popen, PIPE, TimeoutExpired
from time import sleep

if __name__ == '__main__':

    #command_line = "C:\\Progra~1\\PostgreSQL\\12\\bin\\psql.exe -h localhost -d pi -U pi"
    command_line = "sudo hcitool lescan"

    pprint(command_line.split(' '))
    command = command_line.split(' ')

    process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    ret = None
    while True:
        sleep(1)
        print(process.stdout.tell())
        print(process.stdout.read())

    exit(1)

    timer = threading.Event()

    while not timer.wait(1):
        inject_data()

