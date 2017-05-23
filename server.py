#!/usr/bin/env python
from flask import Flask, flash, render_template, session, request, redirect
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import os
from werkzeug.utils import secure_filename

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

UPLOAD_FOLDER = "data/"
ALLOWED_EXTENSIONS = set(["zip", "js"])

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app, async_mode=async_mode)
thread = None


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')


@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


class MyNamespace(Namespace):
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


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':

        # check if the post request has the correct file parts
        if "ZIP_file" not in request.files or "JS_file" not in request.files:
            flash("One or more missing files")
            return redirect(request.url)

        JS_file = request.files["JS_file"]
        ZIP_file = request.files['ZIP_file']

        # check if it might be empty an empty filename which would indicate it is missing
        if ZIP_file.filename == '' or JS_file.filename == '':
            flash('Missing file')
            return redirect(request.url)

        if (ZIP_file and allowed_file(ZIP_file.filename)
                    and JS_file and allowed_file(JS_file.filename)):
            # Gonna want to use custom filenames. use counter?
            JS_filename = secure_filename(JS_file.filename)
            ZIP_filename = secure_filename(ZIP_file.filename)

            JS_file.save(os.path.join(app.config['UPLOAD_FOLDER'], JS_filename))
            ZIP_file.save(os.path.join(app.config['UPLOAD_FOLDER'], ZIP_filename))

            flash("successfully uploaded " + JS_filename + " and " + ZIP_filename )
            return render_template("suc_upload.html")

    # in case the request was made with GET instead of POST
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


socketio.on_namespace(MyNamespace('/test'))

if __name__ == '__main__':
    socketio.run(app, debug=True)
