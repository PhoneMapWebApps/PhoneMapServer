import os

from flask import session, request
from flask_login import current_user
from flask_socketio import Namespace, emit, join_room

from app.main import sql, stats
from app.main.logger import log
from .. import socketio, app

thread = None

ROOT_ID = 1


def background_thread():
    pass


# TODO: reenable error handler later
# @socketio.on_error("/browser")
# def on_error(value):
#     if isinstance(value, KeyError):
#         log("KeyError caught")
#         print(value)
#         emit("error", {'error': "A KeyError has occured. The required data "
#                                 "was not passed, or passed with the wrong names"})
#     else:
#         print(value)
#         raise(value)


def code_available():
    # phone gets new tasks to process
    emit("code_available", broadcast=True, namespace="/phone")


def update_task_list(task_id):
    if not current_user.is_authenticated:
        emit("new_tasks", {'task_id': task_id}, namespace="/browser", broadcast=True)
        return

    # client gets new task list
    emit("new_tasks", {'task_id': task_id}, namespace="/browser", room=current_user.user_id)
    if current_user.user_id != ROOT_ID:
        emit("new_tasks", {'task_id': task_id}, namespace="/browser", room=ROOT_ID)


def update_progbar(task_id):
    task = sql.get_task(task_id).to_json()
    value = task['completed_subtasks'] / task['total_subtasks']

    if not current_user.is_authenticated:
        emit("progbar", {'task_id': task_id, 'value':value}, namespace="/browser", broadcast=True)
        return

    # client gets new task list
    emit("progbar", {'task_id': task_id, 'value':value}, namespace="/browser", room=current_user.user_id)
    if current_user.user_id != ROOT_ID:
        emit("progbar", {'task_id': task_id, 'value':value}, namespace="/browser", room=ROOT_ID)


def delete_task(taskid):
    if not current_user.is_authenticated:
        return

    emit("del_task", {'task_id': taskid}, namespace="/browser", room=current_user.user_id)
    if current_user.user_id != ROOT_ID:
        emit("del_task", {'task_id': taskid}, namespace="/browser", room=ROOT_ID)


def log_and_emit(data, broadcast):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': data, 'count': session['receive_count']},
         broadcast=broadcast)
    log(data)


def send_code(data_file_path, task_id, task_name):
    if not (data_file_path and task_id and task_name):
        emit('no_tasks')
        log_and_emit(BrowserSpace.SERVER_NO_TASKS, True)
        return

    js_file_path = os.path.join(app.config['JS_FOLDER'], str(task_id) + ".js")
    with open(js_file_path, "r") as js_file:
        js_data = js_file.read()
    zip_file_path = os.path.join(data_file_path)
    with open(zip_file_path, "r") as data_file:
        data = data_file.read()
    emit('set_code', {'code': js_data, 'data': data, 'task_name': task_name})


class MainSpace(Namespace):
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
    def on_my_ping():
        emit('my_pong')

    @staticmethod
    def on_my_event(message):
        log_and_emit(message['data'], False)

    @staticmethod
    def on_my_broadcast_event(message):
        log_and_emit(message['data'], True)

    @staticmethod
    def on_get_phones():
        emit('phone_data', {'data': stats.get_workertimes_json()})


class BrowserSpace(MainSpace):
    @staticmethod
    def on_connect():
        global thread
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
        log(BrowserSpace.CLIENT_CONNECT_MSG + request.sid)

        emit('my_response', {'data': BrowserSpace.SERVER_RESPONSE_CON_OK,
                             'count': 0})
        if current_user.is_active:
            join_room(current_user.user_id)

    @staticmethod
    def on_disconnect():
        log(BrowserSpace.CLIENT_DISCNCT_MSG + request.sid)
        emit('my_response', {'data': BrowserSpace.CLIENT_DISCNCT_MSG + request.sid,
                             'count': 0})

    @staticmethod
    def on_get_user_tasks():
        if not current_user.is_authenticated:
            return

        tasks = sql.get_user_tasks(current_user.user_id)
        emit('user_tasks', {'data': tasks, 'replace': False, 'remove': False})

    @staticmethod
    def on_get_user_task_by_id(message):
        task = [sql.get_task(int(message["data"])).to_json()]
        if not task:
            emit('user_tasks', {'remove': True, 'task_id': message["data"]}, broadcast=True)
            return
        emit('user_tasks', {'data': task, 'replace': True, 'remove': False}, broadcast=True)

    @staticmethod
    def on_retry_failed(message):
        sql.restart_failed_tasks(int(message["failed_task_id"]))
        code_available()


class PhoneSpace(MainSpace):
    @staticmethod
    def on_connect():
        global thread
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)
        log(BrowserSpace.CLIENT_CONNECT_MSG + request.sid)

        emit('my_response', {'data': BrowserSpace.SERVER_RESPONSE_CON_OK,
                             'count': 0})

    @staticmethod
    def on_disconnect():
        sql.disconnected(request.sid)
        log(BrowserSpace.CLIENT_DISCNCT_MSG + request.sid)

        emit('my_response', {'data': BrowserSpace.CLIENT_DISCNCT_MSG + request.sid,
                             'count': 0})

    # TODO: refactor android to use this socket instead of HTTP
    @staticmethod
    def on_get_task_list(message=None):
        session['receive_count'] = session.get('receive_count', 0) + 1

        task_list = sql.get_task_list()

        emit('my_response',
             {'data': "Sending a task list",
              'count': session['receive_count']},
             broadcast=True)

        emit('task_list',
             {'list': task_list,
              'count': session['receive_count']})

    @staticmethod
    def on_get_code(message):
        phone_id = message["id"]
        log_and_emit(BrowserSpace.CLIENT_GET_CODE + phone_id, True)

        data_file_path, task_id, task_name = sql.get_next_subtask(phone_id, request.sid)
        send_code(data_file_path, task_id, task_name)

    @staticmethod
    def on_get_code_by_id(message):
        phone_id = message["id"]
        log_and_emit(BrowserSpace.CLIENT_GET_CODE + phone_id, True)
        requested_task_id = message["task_id"]

        # Force task -> if true:
        #           only compute for this task, if nothing else available, do nothing.
        #               else:
        #           this task is preferred
        force_task = message.get("force_task", False)

        data_file_path, task_id, task_name = sql.get_subtask_by_task_id(phone_id,
                                                                   request.sid,
                                                                   requested_task_id)

        if force_task:
            send_code(data_file_path, task_id, task_name)

        elif not (data_file_path and task_id and task_name):
            data_file_path, task_id, task_name = sql.get_next_subtask(phone_id, request.sid)

        send_code(data_file_path, task_id, task_name)

    @staticmethod
    def on_start_code(message):
        phone_id = message["id"]

        if sql.start_task(phone_id):
            log_and_emit(BrowserSpace.CLIENT_CODE_START + phone_id, True)
        else:
            log_and_emit(BrowserSpace.CLIENT_WRONG_START + phone_id, True)
            emit('stop_executing')

    @staticmethod
    def on_execution_failed(message):
        phone_id = message["id"]
        sql.stop_execution(phone_id)
        log_and_emit(phone_id + BrowserSpace.CLIENT_ERROR_EXEC + message['exception'], True)

    @staticmethod
    def on_return(message):
        phone_id = message["id"]
        res = message["return"]
        sql.execution_complete(phone_id, res)

        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': "A subtask has finished", 'count': session['receive_count']},
             broadcast=True)
        log("TASK RETURNED")


socketio.on_namespace(PhoneSpace('/phone'))
socketio.on_namespace(BrowserSpace('/browser'))
