### BEGIN INIT INFO
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

data_source_context = {'host': '192.168.2.178',
                       'dbname': 'pi',
                       'user': 'pi',
                       'password': 'pi'}

DEVICE_ID = 'D2000-00001'

conn = psycopg2.connect(**data_source_context)


def inject_data():
    with conn:
        cur = conn.cursor()

        u = time()
        pm25 = (sin(u / 60) + 1)*100

        print(u, pm25)

        with cur:
            cur.execute("INSERT INTO telemetry (device_id, timestamp, pm25)"
                        "VALUES (%s, %s, %s)", (DEVICE_ID, datetime.now(), pm25))


if __name__ == '__main__':

    timer = threading.Event()

    while not timer.wait(1):
        inject_data()

