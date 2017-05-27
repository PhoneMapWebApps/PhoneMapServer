#!/usr/bin/env python
import os
import zipfile
from flask import Flask, flash, render_template, session, request, redirect
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from werkzeug.utils import secure_filename

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config.from_object('config.Development')

thread = None


def background_thread():
    pass


socketio = SocketIO(app, async_mode=async_mode)


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
        emit('set_id', {'data': 'Connected', 'count': 0, 'id': get_bs_id()})

    # this is hardcoded stuff for testing purposes
    # need to make a queue of which data to send
    def on_get_code(self):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': "someone asked for code", 'count': session['receive_count']},
             broadcast=True)
        with open(app.config['JS_UPLOAD_FOLDER'] + "lol.js", "r") as file:
            js = file.read()
        with open(app.config['ZIP_UPLOAD_FOLDER'] + "extracted_test.zip/file1.txt", "r") as file:
            data = file.read()
        emit('set_code', {'code': js, 'data': data})

    def on_disconnect(self):
        print('Client disconnected', request.sid)


def flashprint(s):
    # flash(s)
    print(s)


def get_bs_id():
    return 42


def request_files_empty(request_result, filetype):
    if request_result.filename == '' or request_result.filename is None:
        flashprint('Empty in submission: ' + filetype)
        return True
    return False


def request_files_missing(request_files, filetype):
    if filetype not in request_files:
        flashprint('Missing from submission: ' + filetype)
        return True
    return False


def request_file_exists(request_files, file_tag):
    return not (
    request_files_missing(request_files, file_tag) or request_files_empty(request_files[file_tag], file_tag))


def file_extension_okay(filename, required_file_extension):
    file_extension = filename.rsplit('.', 1)[1].lower()
    if '.' in filename and file_extension == required_file_extension:
        return True
    flashprint('Expected file extension: ' + required_file_extension + ' but got: ' + file_extension)
    return False


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        js_file_tag = 'JS_FILE'
        zip_file_tag = 'ZIP_FILE'

        flashprint('Checking file existence')
        if not request_file_exists(request.files, js_file_tag): return redirect(request.url)
        if not request_file_exists(request.files, zip_file_tag): return redirect(request.url)

        js_file = request.files[js_file_tag]
        zip_file = request.files[zip_file_tag]

        flashprint('Checking file extensions')
        if not file_extension_okay(js_file.filename, 'js'): return redirect(request.url)
        if not file_extension_okay(zip_file.filename, 'zip'): return redirect(request.url)

        flashprint('Saving and extracting...')
        save_and_extract_files(js_file, zip_file)
        return redirect(request.url)

    flashprint("Error; perhaps you used incorrect file types?")
    return redirect(request.url)


def save_and_extract_files(js_file, zip_file):
    # Gonna want to use custom file_names. Append user_id and put it in a folder for the user/task.
    js_filename = secure_filename(js_file.filename)
    zip_filename = secure_filename(zip_file.filename)
    flashprint('Uploading...')
    js_file.save(os.path.join(app.config['JS_UPLOAD_FOLDER'], js_filename))
    zip_file.save(os.path.join(app.config['ZIP_UPLOAD_FOLDER'], zip_filename))
    flashprint("successfully uploaded " + js_filename + " and " + zip_filename)
    extract(zip_filename)


def extract(filename):
    with zipfile.ZipFile(app.config['ZIP_UPLOAD_FOLDER'] + filename, "r") as zip_ref:
        zip_ref.extractall(app.config['ZIP_UPLOAD_FOLDER'] + "extracted_" + filename + "/")


socketio.on_namespace(PhoneMap('/test'))

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0")
