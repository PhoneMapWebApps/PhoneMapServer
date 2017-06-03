#!/usr/bin/env python
from flask import request, render_template, redirect

from app.main import sql
from app.main.files import request_file_exists, file_extension_okay
from app.main.logger import log
from . import main as app


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
    if not request_file_exists(request.files, js_file_tag):
        return redirect(request.url)
    if not request_file_exists(request.files, zip_file_tag):
        return redirect(request.url)

    js_file = request.files[js_file_tag]
    zip_file = request.files[zip_file_tag]

    log('Checking file extensions')
    if not file_extension_okay(js_file.filename, 'js'):
        return redirect(request.url)
    if not file_extension_okay(zip_file.filename, 'zip'):
        return redirect(request.url)

    # adds to DB and extracts
    sql.add_to_db(js_file, zip_file)

    return redirect(request.url)
