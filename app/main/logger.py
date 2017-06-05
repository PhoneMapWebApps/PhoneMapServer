import os

from datetime import datetime
from flask import flash

# TODO: cleanup
logs_dir = 'logs'
log_filename = 'logs/log.txt'

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

if os.path.isfile(log_filename):
    os.remove(log_filename)

def log(msg):
    # ignore flash if not testing
    try:
        flash(msg)
    except RuntimeError:
        pass
    print(msg)
    log_file = open(log_filename, 'a+')
    log_file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + msg + '\n')
