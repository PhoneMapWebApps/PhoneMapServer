#!/usr/bin/env python3
import os
import zipfile
from flask import Flask, flash, render_template, session, request, redirect
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from flask_sqlalchemy import SQLAlchemy

import files
from database.adapter import db
import database.functions as sql

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.

if not os.path.isfile("config.py"):
    print("Please setup your config.py file. See sampleconfig.py for info.")
    quit()

async_mode = None

app = Flask(__name__)
app.config.from_object('config.Development')

thread = None

# initialise with vals
db.init_app(app)

# use correct app context
with app.app_context():
    db.create_all()

socketio = SocketIO(app, async_mode=async_mode)


def background_thread():
    pass


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


class PhoneMap(Namespace):
    def on_my_event(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']})

    def on_my_broadcast_event(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']},
             broadcast=True)

    def on_join(self, message):
        join_room(message['room'])
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'In rooms: ' + ', '.join(rooms()),
              'count': session['receive_count']})

    def on_leave(self, message):
        leave_room(message['room'])
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'In rooms: ' + ', '.join(rooms()),
              'count': session['receive_count']})

    def on_close_room(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                             'count': session['receive_count']},
             room=message['room'])
        close_room(message['room'])

    def on_my_room_event(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']},
             room=message['room'])

    def on_disconnect_request(self):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'Disconnected!', 'count': session['receive_count']})
        disconnect()

    def on_my_ping(self):
        emit('my_pong')

    def on_connect(self):
        global thread
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
        emit('set_id', {'data': 'Connected', 'count': 0, 'id': get_some_id()})

    # TODO this is hardcoded stuff for testing purposes
    # need to make a queue of which data to send
    def on_get_code(self):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': "someone asked for code", 'count': session['receive_count']},
             broadcast=True)

        # TODO: probably want to specify which task to run, as opposed to just latest task
        # res = sql.get_from_db_by_id(1)
        res = sql.get_latest()

        with open(app.config['JS_UPLOAD_FOLDER'] + res.js_file, "r") as file:
            js = file.read()
        with open(app.config['ZIP_UPLOAD_FOLDER'] + files.EXTRACTED_PREFIX + res.zip_file + "/file1.txt", "r") as file:
            data = file.read()
        emit('set_code', {'code': js, 'data': data})

    def on_execution_failed(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': "Client failed executing with stack trace: " + message['exception'], 'count': session['receive_count']},
             broadcast = True)

    def on_return(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': "Client returns following data: " + message['return'], 'count': session['receive_count']},
             broadcast = True)

    def on_disconnect(self):
        print('Client disconnected', request.sid)


def flashprint(s):
    flash(s)
    print(s)


# TODO: actually get a real proper non-joke ID
def get_some_id():
    return 42


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    # TODO - these hold whatever code/data files were uploaded thorugh the browser
    #        interface last - but there should really be connection between client
    #        id and the code/file pair that belong to it.

    if request.method == 'POST':
        js_file_tag = 'JS_FILE'
        zip_file_tag = 'ZIP_FILE'

        flashprint('Checking file existence')
        if not files.request_file_exists(request.files, js_file_tag): return redirect(request.url)
        if not files.request_file_exists(request.files, zip_file_tag): return redirect(request.url)

        js_file = request.files[js_file_tag]
        zip_file = request.files[zip_file_tag]

        flashprint('Checking file extensions')
        if not files.file_extension_okay(js_file.filename, 'js'): return redirect(request.url)
        if not files.file_extension_okay(zip_file.filename, 'zip'): return redirect(request.url)

        flashprint('Saving and extracting...')
        files.save_and_extract_files(app, js_file, zip_file)

        task_id = sql.add_to_db(js_file, zip_file)

        return redirect(request.url)

    flashprint("Error; perhaps you used incorrect file types?")
    return redirect(request.url)


socketio.on_namespace(PhoneMap('/test'))

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0")
