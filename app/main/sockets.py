from flask import session, request
from flask_socketio import Namespace, emit

from app.main import sql
from app.main.logger import log
from .. import socketio, app


def background_thread():
    pass


thread = None

# TODO: reenable error handler later
# @socketio.on_error("/test")
# def on_error(value):
#     if isinstance(value, KeyError):
#         log("KeyError caught")
#         print(value)
#         emit("error", {'error': "A KeyError has occured. The required data "
#                                 "was not passed, or passed with the wrong names"})
#     else:
#         print(value)
#         raise value


def code_available():
    emit("code_available", broadcast=True, namespace="/test")


def log_and_emit(data, broadcast):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': data, 'count': session['receive_count']},
         broadcast=broadcast)
    log(data)


def send_code(data_file, task_id, task_name):
    if not (data_file and task_id and task_name):
        emit('no_tasks')
        log_and_emit(PhoneMap.SERVER_NO_TASKS, True)
        return

    with open(app.config['JS_FOLDER'] + str(task_id) + ".js", "r") as js_file:
        js_data = js_file.read()
    with open(app.config['ZIP_FOLDER'] + str(task_id) + "/" + data_file, "r") as data_file:
        data = data_file.read()
    emit('set_code', {'code': js_data, 'data': data, 'task_name': task_name})


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
        log_and_emit(message['data'], False)

    @staticmethod
    def on_my_broadcast_event(message):
        log_and_emit(message['data'], True)

    @staticmethod
    def on_get_code(message):
        phone_id = message["id"]
        log_and_emit(PhoneMap.CLIENT_GET_CODE + phone_id, True)

        data_file, task_id, task_name = sql.get_next_subtask(phone_id, request.sid)
        send_code(data_file, task_id, task_name)

    @staticmethod
    def on_get_latest_code(message):
        phone_id = message["id"]
        log_and_emit(PhoneMap.CLIENT_GET_CODE + phone_id, True)

        data_file, task_id, task_name = sql.get_latest_subtask(phone_id, request.sid)
        send_code(data_file, task_id, task_name)

    @staticmethod
    def on_get_code_by_id(message):
        phone_id = message["id"]
        log_and_emit(PhoneMap.CLIENT_GET_CODE + phone_id, True)
        requested_task_id = message["task_id"]

        # Force task -> if true:
        #           only compute for this task, if nothing else available, do nothing.
        #               else:
        #           this task is preferred
        force_task = message.get("force_task", False)

        data_file, task_id, task_name = sql.get_subtask_by_task_id(phone_id,
                                                                   request.sid,
                                                                   requested_task_id)

        if force_task:
            send_code(data_file, task_id, task_name)

        elif not (data_file and task_id and task_name):
            data_file, task_id, task_name = sql.get_next_subtask(phone_id, request.sid)

        send_code(data_file, task_id, task_name)

    @staticmethod
    def on_start_code(message):
        phone_id = message["id"]

        if sql.start_task(phone_id):
            log_and_emit(PhoneMap.CLIENT_CODE_START + phone_id, True)
        else:
            log_and_emit(PhoneMap.CLIENT_WRONG_START + phone_id, True)
            emit('stop_executing')

    @staticmethod
    def on_execution_failed(message):
        phone_id = message["id"]
        sql.stop_execution(phone_id)
        log_and_emit(phone_id + PhoneMap.CLIENT_ERROR_EXEC + message['exception'], True)

    @staticmethod
    def on_return(message):
        phone_id = message["id"]
        sql.execution_complete(phone_id)
        log_and_emit(phone_id + PhoneMap.CLIENT_FINISHED + message['return'], True)

    @staticmethod
    def on_get_task_list(message):
        session['receive_count'] = session.get('receive_count', 0) + 1

        task_list = sql.get_task_list()

        emit('my_response',
             {'data': "Sending a task list",
              'count': session['receive_count']},
             broadcast=True)

        emit('task_list',
             {'list': task_list,
              'count': session['receive_count']})


socketio.on_namespace(PhoneMap('/test'))
