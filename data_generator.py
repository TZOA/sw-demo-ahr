#!/usr/bin/env python3
### BEGIN INIT INFO
# Provides:          data_generator.py
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start daemon at boot time
# Description:       Enable service provided by daemon.
### END INIT INFO

import logging
from random import random

import psycopg2
from time import time
from datetime import datetime
import threading
from math import sin, tan, pi, sqrt
import subprocess
from time import sleep
import socket

# Setup database connection parameters
data_source_context = {'host': '192.168.2.178',
                       'dbname': 'pi',
                       'user': 'pi',
                       'password': 'pi'}

# Device ID for simulated Haven (CAM) data.
DEVICE_ID = 'D2000-00001'

# Make sure to set the correct CAC address in /etc/init.d/netcat_gatttool.sh
# The address(s) can be obtained using 'sudo hcitool lescan | grep CAC'
# BLE Address for HAVEN-CAC-1939-0004 is 3C:71:BF:CC:0C:06

# GATTTOOL_PROXY_ADDRESS = '192.168.2.178'
GATTTOOL_PROXY_ADDRESS = 'localhost'
GATTTOOL_PROXY_PORT    = 1234

# Setup logging
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

# Make the database connection available globally.
conn = None


def connect_to_db():
    global conn

    if conn is not None:
        try:
            cur = conn.cursor()
            with cur:
                cur.execute("SELECT version()")

                # print(cur.fetchone()[0])
        except psycopg2.OperationalError:
            conn = None

    if conn is None:
        try:
            conn = psycopg2.connect(**data_source_context)
            logger.info('Connected to database!')
        except psycopg2.OperationalError:
            conn = None

    if conn is None:
        logger.info('Disconnected from database!')


# Some var's used in inject_data() that need to be persistent.
decay = 0
pm25n = 0
u0 = 0
u1 = 150
fan_state = False


def inject_data():
    global conn
    global decay
    global pm25n
    global fan_state
    global u0
    global u1

    connect_to_db()

    if conn is None:
        return

    try:
        with conn:
            cur = conn.cursor()

            u = time()*2*pi

            # Here you can tweak the look of the simulated data.
            airflow     = sin(u / 3600)*0.3 + sin(u / (60 * 17))*0.02 + sin(u / (60 * 73))*0.08 + 0.3 + random() * 0.05
            temperature = sin(u / 3600)*3 + sin(u / (60*17))*0.2 + sin(u / (60*73))*0.8 + 18 + random()*1
            pressure    = sin(u / 7200)*100 + sin(u / (60*48))*5 + sin(u / (60*156))*20 + 1000 + random()*1
            humidity    = sin(u / 1900)*20 + sin(u / (60*44))*5 + sin(u / (60*277))*10 + 40 + random()*1
            voc         = sin(u / 3600)*100 + sin(u / (60*17))*20 + sin(u / (60*73))*8 + 150 + random()*5
            co2         = sin(u / 3600)*200 + sin(u / (60*66))*60 + sin(u / (60*149))*120 + 407 + random()*3

            # PM2.5
            if time() - u0 > 300:
                pm25n = random()*300 + 200
                decay = 50
                u0 = time()

            pm25n = pm25n - decay

            decay = decay * 0.85

            if pm25n < 10:
                pm25n = 10

            pm25 = pm25n + sin(u / (60*2.3))*9 + sin(u / (60*5.6))*17 + random()*20 + 25

            if pm25 < 0:
                pm25 = 0


            # VOC
            if time() - u1 > 300:
                u1 = 0
            if u1 < 100:
                voc = voc + sin(u1/100*pi*2)*600

            # Fan State
            if (pm25 > 100 or voc > 600) and fan_state is False:
                logger.info('Setting fan state to ON.')
                fan_state = True
                set_cac_fan_state_with_retry(fan_state)

            if (pm25 < 50 and voc < 400) and fan_state is True:
                logger.info('Setting fan state to OFF.')
                fan_state = False
                set_cac_fan_state_with_retry(fan_state)

            if fan_state is True:
                airflow = airflow + 8 + random() * 2

            # print(u, temperature, airflow, pressure, humidity, voc, co2, pm25, fan_state)

            # Cast fan_state as Grafana and DB need it to be an integer for graphing.
            if fan_state is True:
                fan_state = 1
            else:
                fan_state = 0

            # Write the data to the database.
            logger.info('Inserting data...')
            with cur:
                cur.execute("INSERT INTO telemetry (device_id, timestamp, "
                            "temperature, airflow, pressure, humidity, voc, co2, pm25_mc, fan_state)"
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (DEVICE_ID, datetime.now(),
                             temperature, airflow, pressure, humidity, voc, co2, pm25, fan_state))

    # If we encounter any problem invalidate the database connection so we retry it.
    except psycopg2.OperationalError:
        conn = None


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
        subprocess.run(['sudo', 'killall', '-q', '-v', 'gatttool'])
    except FileNotFoundError:
        logger.info('Failed to run killall on gatttool.')
        return False

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
        return False

    except ConnectionRefusedError:
        logger.warning('Timeout trying to connect to gatttool/netcat.')
        return False

    except ConnectionResetError:
        logger.warning('Connection reset while communicating with gatttool/netcat.')
        return False

    return True


def set_cac_fan_state_with_retry(fan_on, retries=5):
    while not set_cac_fan_state(fan_on) and retries > 0:
        logger.warning('Failed to set cac fan state, retrying... (%s)' % retries)
        retries = retries - 1
        sleep(0.5)

    if retries == 0:
        return False
    return True


if __name__ == '__main__':

    '''
    while True:
        set_cac_fan_state_with_retry(True)
        sleep(15)

        set_cac_fan_state_with_retry(False)
        sleep(15)

    exit(1)
    '''
    timer = threading.Event()

    while not timer.wait(1):
        inject_data()

# End of file.
