from urllib.parse import urlparse, urljoin

from flask import request, render_template, redirect, jsonify, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user

from app import login_manager
from app.main import sql
from app.main.files import request_file_exists, file_extension_okay, flashmsg
from app.main.logger import log, log_filename
from app.main.sockets import code_available, update_task_list

from . import main as app


@app.route('/monitor')
@login_required
def monitor():
    try:
        log_file = open(log_filename, 'r')
        log_lines = log_file.readlines()
    except FileNotFoundError:
        log_lines = ""

    return render_template('monitor.html', console_old=log_lines)


def is_safe_url(next_url):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, next_url))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = sql.authenticate_user(username, password)
        if user:
            log("Successful login for " + username + " with id " + str(user.user_id))
            login_user(user)
            next_url = request.args.get('next')

            return redirect(next_url or url_for('main.index'))
        else:
            log("Incorrect login for user " + username)
            return render_template('login.html', badlogin=True)
    else:
        return render_template('login.html')


@app.route("/create", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        username = request.form['username']
        if username == "":
            return render_template("create.html", issue=True)
        password = request.form['password']
        if len(password) < 6:
            return render_template("create.html", issue=True)

        exists = sql.does_user_exist(username)
        if exists:
            log("User " + username + " already exists, please choose another name")
            return render_template("create.html", exists=True)
        else:
            fullname = request.form["fullname"]
            organisation = request.form["organisation"]
            user = sql.add_user(username, password, fullname, organisation)
            login_user(user)
            return redirect(url_for("main.index"))
    else:
        return render_template("create.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    # return redirect(somewhere)
    log("Logged out")
    return redirect(url_for("main.index"))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/tasklist')
def get_task_list():
    task_list = sql.get_task_list()
    return jsonify(task_list)


# upload task to db
@app.route('/tasks', methods=['POST'])
@login_required
def upload_file():
    js_file_tag = 'JS_FILE'
    zip_file_tag = 'ZIP_FILE'
    task_name_tag = 'TASK_NAME'
    task_desc_tag = 'TASK_DESC'

    flash('Checking file existence...')
    if not request_file_exists(request.files, js_file_tag):
        return redirect(url_for('main.index'))
    if not request_file_exists(request.files, zip_file_tag):
        return redirect(url_for('main.index'))

    js_file = request.files[js_file_tag]
    zip_file = request.files[zip_file_tag]
    task_name = request.values[task_name_tag]
    task_desc = request.values[task_desc_tag]

    if not (len(task_name) and len(task_desc)):
        flashmsg('Missing task name or task description!')
    if len(task_name) > 255:
        flashmsg('Task name is too long')
        return redirect(url_for('main.index'))
    flashmsg('Checking file extensions...')
    if not file_extension_okay(js_file.filename, 'js'):
        return redirect(url_for('main.index'))
    if not file_extension_okay(zip_file.filename, 'zip'):
        return redirect(url_for('main.index'))

    no_tasks_currently = not sql.get_task_list()
    # adds to DB and extracts
    sql.add_to_db(current_user.user_id, js_file, zip_file, task_name, task_desc)
    log('Uploaded new task ' + task_name + ' (' + js_file.filename + ' ' + zip_file.filename + ')')

    update_task_list()

    if no_tasks_currently:
        code_available()

    return redirect(url_for('main.index'))


@app.route('/tasks/<task_id>', methods=['POST'])
@login_required
def change_files(task_id):
    if not allowed_user(task_id):
        return ""

    js_file_tag = 'JS_FILE'
    zip_file_tag = 'ZIP_FILE'

    if request_file_exists(request.files, js_file_tag):
        # update code
        js_file = request.files[js_file_tag]

        if not file_extension_okay(js_file.filename, 'js'):
            return redirect(url_for('main.index'))

        flashmsg("Updating code")
        sql.update_code_in_db(task_id, js_file)
        flashmsg("Code updated successfully")

    if request_file_exists(request.files, zip_file_tag):
        # update data
        zip_file = request.files[zip_file_tag]

        if not file_extension_okay(zip_file.filename, 'zip'):
            return redirect(url_for('main.index'))

        flashmsg("Updating data for task")
        sql.update_data_in_db(task_id, zip_file)
        flashmsg("Data updated successfully")

    log('Updated task code or data, task id ' + task_id)

    return redirect(url_for('main.index'))


@app.route('/tasks/del/<task_id>', methods=['POST'])
@login_required
def remove_task(task_id):
    if not allowed_user(task_id):
        return "You don't have access to this"

    sql.remove_from_db(task_id)
    return redirect(url_for('main.index'))


@login_manager.user_loader
def user_loader(user_id):
    return sql.get_user(user_id)


@login_manager.unauthorized_handler
def unauthorised():
    return render_template('login.html')


def allowed_user(task_id):
    # Check if valid user
    curr_id = current_user.user_id
    task = sql.get_task(task_id)
    # 1 == root
    return not (curr_id != 1 and task.owner_id != curr_id)
