from flask import session, request, current_app as app
from flask_socketio import Namespace, emit

from app.main import sql
from app.main.logger import log
from .. import socketio


def background_thread():
    pass


thread = None


@socketio.on_error("/test")
def on_error(value):
    if isinstance(value, KeyError):
        log("KeyError caught")
        emit("error", {'error': "A KeyError has occured. The required data "
                                "was not passed, or passed with the wrong names"})
    else:
        raise value

def log_and_emit(session, data, broadcast):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': data, 'count': session['receive_count']},
        broadcast=broadcast)
    log(data)

class PhoneMap(Namespace):
    CLIENT_CONNECT_MSG = "New agent has connected with request ID: "
    CLIENT_DISCNCT_MSG = "Agent has disconnected, request ID: "
    CLIENT_GET_CODE = "Agent has asked for code, agent ID: "
    CLIENT_CODE_START = "Agent has started executing the code, agent ID: "
    CLIENT_WRONG_START = "Agent has tried to start wrong code, agent ID: "
    CLIENT_ERROR_EXEC = " agent failed executing with the stack trace:\n "
    CLIENT_FINISHED = " agent has finished with following return: "
    SERVER_NO_TASKS = "Client requested code, but no tasks are available! Agent ID: "

    SERVER_RESPONSE_CON_OK = "CON_OK"

    @staticmethod
    def on_connect():
        global thread
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
        log(PhoneMap.CLIENT_CONNECT_MSG + request.sid)
        emit('my_response', {'data': PhoneMap.SERVER_RESPONSE_CON_OK,
                             'count': 0})

    @staticmethod
    def on_disconnect():
        sql.disconnected(request.sid)
        log(PhoneMap.CLIENT_DISCNCT_MSG + request.sid)
        emit('my_response', {'data': PhoneMap.CLIENT_DISCNCT_MSG + request.sid,
                             'count': 0})

    @staticmethod
    def on_my_ping():
        emit('my_pong')

    @staticmethod
    def on_my_event(message):
        log_and_emit(session, message['data'], False)

    @staticmethod
    def on_my_broadcast_event(message):
        log_and_emit(session, message['data'], True)

    @staticmethod
    def on_get_code(message):
        phone_id = message["id"]
        log_and_emit(session, PhoneMap.CLIENT_GET_CODE + phone_id, True)
        data_file, task_id = sql.get_next_subtask(phone_id, request.sid)

        if not (data_file and task_id):
            emit('no_tasks')
            log_and_emit(session, PhoneMap.SERVER_NO_TASKS + phone_id, True)
            return

        with open(app.config['JS_FOLDER'] + str(task_id) + ".js", "r") as js_file:
            js_data = js_file.read()
        with open(app.config['ZIP_FOLDER'] + str(task_id) + "/" + data_file, "r") as data_file:
            data = data_file.read()
        emit('set_code', {'code': js_data, 'data': data})

    @staticmethod
    def on_start_code(message):
        phone_id = message["id"]

        if sql.start_task(phone_id):
            log_and_emit(session, PhoneMap.CLIENT_CODE_START + phone_id, True)
        else:
            log_and_emit(session, PhoneMap.CLIENT_WRONG_START + phone_id, True)
            emit('stop_executing')

    @staticmethod
    def on_execution_failed(message):
        phone_id = message["id"]
        sql.stop_execution(phone_id)
        log_and_emit(session, phone_id + PhoneMap.CLIENT_ERROR_EXEC + message['exception'], True)

    @staticmethod
    def on_return(message):
        phone_id = message["id"]
        sql.execution_complete(phone_id)
        log_and_emit(session, phone_id + PhoneMap.CLIENT_FINISHED + message['return'], True)


socketio.on_namespace(PhoneMap('/test'))
