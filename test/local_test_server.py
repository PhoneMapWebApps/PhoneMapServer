import os
import subprocess
import time

from nose.tools import nottest

CONFIG_FILE = "config.py"
BACKUP_EXT = ".bak"

@nottest
def create_test_config_file():
    file = open(CONFIG_FILE, "w")
    file.write("class Development(object):\n")
    file.write("    DEBUG = True\n")
    file.write("    SQLALCHEMY_DATABASE_URI = \"sqlite:///:memory:\"\n")
    file.write("    SQLALCHEMY_TRACK_MODIFICATIONS = False\n")
    file.write("    JS_UPLOAD_FOLDER = \"test/upload/data/js/\"\n")
    file.write("    ZIP_UPLOAD_FOLDER = \"test/upload/data/zip/\"\n")
    file.close()


@nottest
def start_local_test_server():
    # backup current config file
    if(os.path.isfile(CONFIG_FILE)):
        os.rename(CONFIG_FILE, CONFIG_FILE + BACKUP_EXT)

    create_test_config_file()

    proc = subprocess.Popen("FLASK_APP=./run.py flask run", shell = True)
    time.sleep(1.0)
    return proc

@nottest
def stop_local_test_server(test_server):
    test_server.kill()

    # restore original config file
    if (os.path.isfile(CONFIG_FILE + BACKUP_EXT)):
        os.remove(CONFIG_FILE)
        os.rename(CONFIG_FILE + BACKUP_EXT, CONFIG_FILE)
