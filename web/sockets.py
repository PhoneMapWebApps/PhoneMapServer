#!/usr/bin/env python
from flask import Flask, flash, render_template, session, request, redirect
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect

from web.webapp import app
from database.adapter import db
import database.functions as sql
import files


async_mode = None
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

def background_thread():
    pass


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

# TODO: actually get a real proper non-joke ID
def get_some_id():
    return 42


socketio.on_namespace(PhoneMap('/test'))
