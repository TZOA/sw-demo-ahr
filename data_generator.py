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
from math import sin

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

            u = time()
            pm25 = (sin(u / 60) + 1)*100

            print(u, pm25)

            with cur:
                cur.execute("INSERT INTO telemetry (device_id, timestamp, pm25)"
                            "VALUES (%s, %s, %s)", (DEVICE_ID, datetime.now(), pm25))

    except psycopg2.OperationalError:
        conn = None

from bluetooth.ble import DiscoveryService

if __name__ == '__main__':

    service = DiscoveryService()
    devices = service.discover(2)

    for address, name in devices.items():
        print("Name: {}, address: {}".format(name, address))

    exit(1)

    timer = threading.Event()

    while not timer.wait(1):
        inject_data()

