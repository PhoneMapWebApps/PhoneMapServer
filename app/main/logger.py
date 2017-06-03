import os

from flask import flash

# TODO: cleanup
logs_dir = 'logs'
log_filename = 'logs/log.txt'

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

if os.path.isfile(log_filename):
    os.remove(log_filename)

log_file = open(log_filename, 'a+')


def log(msg):
    # ignore flash if not testing
    try:
        flash(msg)
    except RuntimeError:
        pass
    log_file.write(msg + '\n')
    log_file.flush()
