import os

from datetime import datetime

# TODO: cleanup
logs_dir = 'logs'
log_filename = 'logs/log.txt'

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

if os.path.isfile(log_filename):
    os.remove(log_filename)


def log(msg):
    print(msg)
    log_file = open(log_filename, 'a+')
    log_file.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + msg + '\n')
