#!/usr/bin/env python3

import os

from app import create_app, socketio, app

if not os.path.isfile("config.py"):
    print("Please setup your config.py file. See sampleconfig.py for info.")
    quit()

debug = True
host = "0.0.0.0"
create_app(debug=debug)

if __name__ == '__main__':
    socketio.run(app, debug=debug, host=host)
