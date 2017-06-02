#!/usr/bin/env python
from flask import session, request
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect

import database.functions as sql
from misc.files import EXTRACTED_PREFIX
from misc.logger import log
from web.webapp import app

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

    def on_disconnect_request(self, message=None):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'Disconnected!', 'count': session['receive_count']})
        disconnect()

    def on_my_ping(self, message=None):
        emit('my_pong')

    def on_connect(self, message=None):
        global thread
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
        emit('my_response', {'data': 'Connected', 'count': 0})

    def on_get_code(self, message=None):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': "Someone asked for code", 'count': session['receive_count']},
             broadcast=True)

        data_file, zip_file, js_file = sql.get_next(message["id"], request.sid)

        if not (data_file and zip_file and js_file):
            log("Tasks all gone")
            emit('no_tasks')
            return

        with open(app.config['JS_UPLOAD_FOLDER'] + js_file, "r") as file:
            js = file.read()
        with open(app.config['ZIP_UPLOAD_FOLDER'] + EXTRACTED_PREFIX + zip_file + "/" + data_file, "r") as file:
            data = file.read()
        emit('set_code', {'code': js, 'data': data})

    def on_start_code(self, message=None):
        session['receive_count'] = session.get('receive_count', 0) + 1

        log("Starting code...")
        status = sql.start_task(message["id"])
        if status:
            log("Code marked as started.")
            emit('my_response',
                 {'data': "Code started", 'count': session['receive_count']},
                 broadcast = True)
        else:
            log("Code already running or unknown subtask_id, please stop.")
            emit('stop_executing')


    def on_execution_failed(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1

        sql.stop_execution(message["id"])

        emit('my_response',
             {'data': "Client failed executing with stack trace: " + message['exception'], 'count': session['receive_count']},
             broadcast = True)

    def on_return(self, message):
        session['receive_count'] = session.get('receive_count', 0) + 1

        sql.execution_complete(message["id"])

        emit('my_response',
             {'data': "Client returned following data: " + message['return'], 'count': session['receive_count']},
             broadcast = True)

    def on_disconnect(self, message=None):
        sql.disconnected(request.sid)
        print('Client disconnected', request.sid)


socketio.on_namespace(PhoneMap('/test'))
