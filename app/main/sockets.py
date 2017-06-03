from flask import current_app as app
from flask import session, request
from flask_socketio import Namespace, emit

from app.main import sql
from app.main.logger import log
from .. import socketio


def background_thread():
    pass


thread = None


class PhoneMap(Namespace):
    @staticmethod
    def on_my_event(message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']})

    @staticmethod
    def on_my_broadcast_event(message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']},
             broadcast=True)

    @staticmethod
    def on_my_ping():
        emit('my_pong')

    @staticmethod
    def on_connect():
        global thread
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
        emit('my_response', {'data': 'Connected', 'count': 0})

    @staticmethod
    def on_get_code(message=None):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': "Someone asked for code", 'count': session['receive_count']},
             broadcast=True)

        data_file, task_id = sql.get_next(message["id"], request.sid)

        if not (data_file and task_id):
            log("Tasks all gone")
            emit('no_tasks')
            return

        with open(app.config['JS_FOLDER'] + str(task_id) + ".js", "r") as js_file:
            js_data = js_file.read()
        with open(app.config['ZIP_FOLDER'] + str(task_id) + "/" + data_file, "r") as data_file:
            data = data_file.read()
        emit('set_code', {'code': js_data, 'data': data})

    @staticmethod
    def on_start_code(message=None):
        session['receive_count'] = session.get('receive_count', 0) + 1

        log("Starting code...")
        status = sql.start_task(message["id"])
        if status:
            log("Code marked as started.")
            emit('my_response',
                 {'data': "Code started", 'count': session['receive_count']},
                 broadcast=True)
        else:
            log("Code already running or unknown subtask_id, please stop.")
            emit('stop_executing')

    @staticmethod
    def on_execution_failed(message):
        session['receive_count'] = session.get('receive_count', 0) + 1

        sql.stop_execution(message["id"])

        emit('my_response',
             {'data': "Client failed executing with stack trace: " + message['exception'],
              'count': session['receive_count']},
             broadcast=True)

    @staticmethod
    def on_return(message):
        session['receive_count'] = session.get('receive_count', 0) + 1

        sql.execution_complete(message["id"])

        emit('my_response',
             {'data': "Client returned following data: " + message['return'],
              'count': session['receive_count']},
             broadcast=True)

    @staticmethod
    def on_disconnect():
        sql.disconnected(request.sid)
        print('Client disconnected', request.sid)


socketio.on_namespace(PhoneMap('/test'))
