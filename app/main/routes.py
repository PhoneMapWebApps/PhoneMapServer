#!/usr/bin/env python
from flask import request, render_template, redirect, jsonify

from app.main import sql
from app.main.files import request_file_exists, file_extension_okay
from app.main.logger import log, log_filename
from . import main as app


@app.route('/')
def index():
    try:
        log_file = open(log_filename, 'r')
        log_lines = log_file.readlines()
    except FileNotFoundError:
        log_lines = ""

    return render_template('index.html', console_old=log_lines)


@app.route('/tasks')
def tasks():
    all_tasks = sql.get_all_tasks()
    return render_template('tasks.html', task_list=all_tasks)


@app.route('/tasklist')
def get_task_list():
    task_list = sql.get_task_list()
    return jsonify(task_list)


@app.route('/tasks', methods=['POST'])
def upload_file():
    js_file_tag = 'JS_FILE'
    zip_file_tag = 'ZIP_FILE'
    task_name_tag = 'TASK_NAME'
    task_desc_tag = 'TASK_DESC'

    log('Checking file existence')
    if not request_file_exists(request.files, js_file_tag):
        return redirect(request.url)
    if not request_file_exists(request.files, zip_file_tag):
        return redirect(request.url)

    js_file = request.files[js_file_tag]
    zip_file = request.files[zip_file_tag]
    task_name = request.values[task_name_tag]
    task_desc = request.values[task_desc_tag]

    if not (len(task_name) and len(task_desc)):
        log('Must have a task Name and task Desc!')
    if len(task_name) > 255:
        log('task name too long')
        return redirect(request.url)
    log('Checking file extensions')
    if not file_extension_okay(js_file.filename, 'js'):
        return redirect(request.url)
    if not file_extension_okay(zip_file.filename, 'zip'):
        return redirect(request.url)

    # adds to DB and extracts
    sql.add_to_db(js_file, zip_file, task_name, task_desc)

    return redirect(request.url)
