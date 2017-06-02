import os

logs_dir = 'logs'

if not os.path.exists('logs'):
    os.makedirs('logs')

log_file = open('logs/log.txt', 'a+')


def log(s):
    log_file.write(s + '\n')
    log_file.flush()
