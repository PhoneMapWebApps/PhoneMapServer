import os

from flask import flash

logs_dir = 'logs'
log_filename = 'logs/log.txt'

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

if os.path.isfile(log_filename):
    os.remove(log_filename)

log_file = open(log_filename, 'a+')


def log(s):
    flash(s)
    log_file.write(s + '\n')
    log_file.flush()
