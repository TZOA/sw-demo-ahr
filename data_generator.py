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

import logging
import psycopg2
from pprint import pprint
from time import time
from datetime import datetime
import threading
from math import sin, pi
import subprocess


data_source_context = {'host': 'localhost',
                       'dbname': 'pi',
                       'user': 'pi',
                       'password': 'pi'}

DEVICE_ID = 'D2000-00001'

# Make sure to set the correct address in /etc/
# BLE Address for HAVEN-CAC-1939-0004 is 3C:71:BF:CC:0C:06

# GATTTOOL_PROXY_ADDRESS = '192.168.2.178'
GATTTOOL_PROXY_ADDRESS = 'localhost'
GATTTOOL_PROXY_PORT    = 1234

conn = None

logger = logging.getLogger('data_generator')
logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler('/var/log/data_generator.log')
fh.setLevel(logging.INFO)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


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

from time import sleep
import socket


def wait_for(sock, target, timeout=50):
    buffer = ''

    while target not in buffer:
        try:
            buffer = buffer + str(sock.recv(1024))
        except socket.timeout:
            pass

        if timeout <= 0:
            return False, buffer

        timeout = timeout - 1

    return True, buffer


def extract_int(target, buffer):
    # Find the target string in buffer, then grab the following integer.
    n = buffer.find(target)
    n = n + len(target)
    buffer = buffer[n + 1:n + 3]

    # This could be made way more robust, but for now it works...
    '''
    match = re.search(r'tor\s*(\d+)' % target, buffer)
    print(target, buffer)
    match = re.search(r'\D*tor\s*(\d+)', buffer)
    if match:
        print(match.group(1))
    '''

    # If we found an integer, convert and return it, otherwise just bail and return 0
    try:
        return int(buffer)
    except ValueError:
        return 0


# This function will set the CAC's fan override using gatttool proxied through netcat.
def set_cac_fan_state(fan_on):
    # First, make sure no hung or timed out instances of gatttool are running.
    try:
        subprocess.run(['sudo', 'killall', 'gatttool'])
    except FileNotFoundError:
        logger.info('Failed to run killall on gatttool.')
        pass  # Ignore if running on a Windows dev box.

    # Next, set the fan state.  It's very important that gatttool and the CAC has this
    # parameter formatted as a %02d !!
    if fan_on:
        next_fan_state = b'01'  # ON
    else:
        next_fan_state = b'02'  # OFF

    # Now, open a socket to gatttool, which is being proxied by netcat through a TCP socket.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((GATTTOOL_PROXY_ADDRESS, GATTTOOL_PROXY_PORT))

            # Make sure reads are non-blocking with a very short timeout.
            s.setblocking(False)
            s.settimeout(0.1)

            # Now we're going to issue a bunch of command/response type interactions with gatttool
            # If anything goes wrong, we timeout, log the fact, and do nothing else...
            if not wait_for(s, '[LE]>')[0]:
                raise TimeoutError

            logger.info('Attached to gatttool.')

            s.send(b'connect\n')

            if not wait_for(s, 'Connection successful')[0]:
                raise TimeoutError
            logger.info('Connected to CAC.')

            s.send(b'char-read-hnd 3c\n')

            ret = wait_for(s, 'Characteristic value/descriptor:')
            if not ret[0]:
                raise TimeoutError
            logger.info('Fan state override: %s' % extract_int('descriptor:', ret[1]))

            s.send(b'char-write-cmd 3c %s\n' % next_fan_state)

            logger.info('Setting fan state to: %s' % next_fan_state)

            if not wait_for(s, '[LE]>')[0]:
                raise TimeoutError

            s.send(b'char-read-hnd 3c\n')

            ret = wait_for(s, 'Characteristic value/descriptor:')
            if not ret[0]:
                raise TimeoutError
            logger.info('Fan state override: %s' % extract_int('descriptor:', ret[1]))

            s.send(b'disconnect\n')

            if not wait_for(s, '[LE]>')[0]:
                raise TimeoutError

            logger.info('Disconnected from CAC.')

            s.send(b'exit\n\n')

    except TimeoutError:
        logger.warning('Timeout trying to interact with CAC.')

    except ConnectionRefusedError:
        logger.warning('Timeout trying to connect to gatttool/netcat.')

    except ConnectionResetError:
        logger.warning('Connection reset while communicating with gatttool/netcat.')


if __name__ == '__main__':

    while True:
        set_cac_fan_state(True)
        sleep(15)
        set_cac_fan_state(False)
        sleep(15)

    exit(1)

    timer = threading.Event()

    while not timer.wait(1):
        inject_data()

# End of file.
