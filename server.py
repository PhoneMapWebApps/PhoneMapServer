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

JS_UPLOAD_FOLDER = "data/js/"
ZIP_UPLOAD_FOLDER = "data/zip/"
ALLOWED_EXTENSIONS = {"zip", "js"}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['JS_UPLOAD_FOLDER'] = JS_UPLOAD_FOLDER
app.config['ZIP_UPLOAD_FOLDER'] = ZIP_UPLOAD_FOLDER
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
        emit('my_response', {'data': 'Connected', 'count': 0})

    def on_disconnect(self):
        print('Client disconnected', request.sid)


def check_empty(requestResult, filetype):
    if requestResult.filename == '':
        flash('Empty in submission: ' + filetype)
        return True
    return False


def check_missing(request_files, filetype):
    if filetype not in request_files:
        flash('Missing from submission: ' + filetype)
        return True
    return False


def check_valid(request_files, file_tag):
    return check_missing(request_files, file_tag) or check_empty(request_files[file_tag], file_tag)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        js_file_tag = 'JS_FILE'
        zip_file_tag = 'ZIP_FILE'

        if check_valid(request.files, js_file_tag): return redirect(request.url)
        if check_valid(request.files, zip_file_tag): return redirect(request.url)

        JS_file = request.files[js_file_tag]
        ZIP_file = request.files[zip_file_tag]

        if (ZIP_file and allowed_file(ZIP_file.filename) and JS_file and allowed_file(JS_file.filename)):
            # Gonna want to use custom filenames. use counter?
            JS_filename = secure_filename(JS_file.filename)
            ZIP_filename = secure_filename(ZIP_file.filename)

            JS_file.save(os.path.join(app.config['JS_UPLOAD_FOLDER'], JS_filename))
            ZIP_file.save(os.path.join(app.config['ZIP_UPLOAD_FOLDER'], ZIP_filename))

            flash("successfully uploaded " + JS_filename + " and " + ZIP_filename)
            print("successfully uploaded " + JS_filename + " and " + ZIP_filename)

            extract(ZIP_filename)

            return redirect(request.url)

    flash("Error; perhaps you used incorrect file types?")
    return redirect(request.url)


def extract(filename):
    with zipfile.ZipFile(ZIP_UPLOAD_FOLDER + filename, "r") as zip_ref:
        zip_ref.extractall(ZIP_UPLOAD_FOLDER + "extracted_" + filename + "/")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


socketio.on_namespace(PhoneMap('/test'))

if __name__ == '__main__':
    socketio.run(app, debug=True, host="0.0.0.0")
