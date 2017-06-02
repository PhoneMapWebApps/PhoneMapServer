log_file = open("logs/log.txt", "a+")


def log(s):
    log_file.write(s + "\n")
    log_file.flush()
