import os
from web.sockets import socketio
from web.sockets import app


if not os.path.isfile("config.py"):
    print("Please setup your config.py file. See sampleconfig.py for info.")
    quit()


if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0")
