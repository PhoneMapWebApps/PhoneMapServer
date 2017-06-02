from flask import Flask, render_template, request, redirect

import database.functions as sql
from database.adapter import db
from misc.files import request_file_exists, file_extension_okay, \
    save_and_extract_files
from misc.logger import log

app = Flask(__name__)
app.config.from_object("config.Development")

db.init_app(app)

# use correct app context
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tasks')
def tasks():
    return render_template('tasks.html')


@app.route('/tasks', methods=['POST'])
def upload_file():
    js_file_tag = 'JS_FILE'
    zip_file_tag = 'ZIP_FILE'

    log('Checking file existence')
    if not request_file_exists(request.files, js_file_tag): return redirect(request.url)
    if not request_file_exists(request.files, zip_file_tag): return redirect(request.url)

    js_file = request.files[js_file_tag]
    zip_file = request.files[zip_file_tag]

    log('Checking file extensions')
    if not file_extension_okay(js_file.filename, 'js'): return redirect(request.url)
    if not file_extension_okay(zip_file.filename, 'zip'): return redirect(request.url)

    log('Saving and extracting...')
    save_and_extract_files(app, js_file, zip_file)

    # TODO: idk, we probably want the task ID for something at some point
    task_id = sql.add_to_db(app, js_file, zip_file)

    return redirect(request.url)
