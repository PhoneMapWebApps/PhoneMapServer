import os

import shutil

from flask import url_for
from flask_login import current_user
from nose.tools import nottest

from app import socketio, app, db
from app.main.models import Users
from app.main.sockets import PhoneMap
from test.test import BaseTestCase


class TestVanillaSockets(BaseTestCase):
    def test_connect(self):
        client = socketio.test_client(app, "/test")
        received = client.get_received("/test")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["args"][0]["data"], PhoneMap.SERVER_RESPONSE_CON_OK)
        client.disconnect("/test")

    def test_disconnect_reconnect(self):
        client = socketio.test_client(app, "/test")
        # clear received queue
        client.get_received("/test")
        # reconnect
        client.disconnect("/test")
        client.connect("/test")
        received = client.get_received("/test")

        self.assertEqual(len(received), 2)
        self.assertEqual(received[0]["name"], "my_response")
        self.assertEqual(received[1]["args"][0]["data"], PhoneMap.SERVER_RESPONSE_CON_OK)

        client.emit("my_event", {"data": "junk"}, namespace="/test")
        snd_received = client.get_received("/test")

        self.assertEqual(len(snd_received), 1)
        self.assertEqual(len(snd_received[0]["args"]), 1)
        self.assertEqual(snd_received[0]["args"][0]["data"], "junk")

    def test_emit(self):
        client = socketio.test_client(app, "/test")
        client.get_received("/test")
        client.emit("my_event", {"data": "this is good data"}, namespace="/test")
        received = client.get_received("/test")

        self.assertEqual(len(received), 1)
        self.assertEqual(len(received[0]["args"]), 1)
        self.assertEqual(received[0]["name"], "my_response")
        self.assertEqual(received[0]["args"][0]["data"], "this is good data")

    def test_broadcast(self):
        client1 = socketio.test_client(app, "/test")
        client2 = socketio.test_client(app, "/test")
        client3 = socketio.test_client(app)  # other ns, wont receive

        client1.get_received("/test")
        client2.get_received("/test")
        client3.get_received()

        client1.emit("my_broadcast_event", {"data": "42"}, namespace="/test")
        received_1 = client1.get_received("/test")
        received_2 = client2.get_received("/test")

        self.assertFalse(client3.get_received())
        self.assertEqual(len(received_1), 1)
        self.assertEqual(len(received_2), 1)
        self.assertEqual(received_1[0]['name'], "my_response")
        self.assertEqual(received_1[0]["args"][0]["data"], "42")
        self.assertEqual(received_2[0]['name'], "my_response")
        self.assertEqual(received_2[0]["args"][0]["data"], "42")

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()


class TestGetAndStartSockets(BaseTestCase):
    @nottest
    def login_and_upload_data(self):
        user = Users("Test", "pw", "MEGAAAA USERRRR")
        db.session.add(user)
        db.session.commit()
        resp = self.client.post(url_for('main.login'),
                                data={'username': "Test", 'password': "pw"})

        self.assertTrue(current_user.username == 'Test')
        self.assertFalse(current_user.is_anonymous)

        with open('test/resources/test.js', 'rb') as js_file:
            with open('test/resources/test.zip', 'rb') as zip_file:
                resp = self.client.post(
                    '/tasks',
                    data=dict(
                        JS_FILE=js_file,
                        ZIP_FILE=zip_file,
                        TASK_NAME="Some Test Task",
                        TASK_DESC="Interesting description"
                    ),
                    content_type='multipart/form-data'
                )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(os.path.isfile(app.config['JS_FOLDER'] + '1.js'))
        self.assertTrue(os.path.isfile(app.config['ZIP_FOLDER'] + '1.zip'))
        self.assertTrue(os.path.isdir(app.config['ZIP_FOLDER'] + '1'))
        return resp

    @nottest
    def delete_data(self):
        os.remove(app.config['JS_FOLDER'] + '1.js')
        os.remove(app.config['ZIP_FOLDER'] + '1.zip')
        shutil.rmtree(app.config['ZIP_FOLDER'] + '1')

    def test_get_and_start_code(self):
        with app.app_context():
            with self.client:
                self.login_and_upload_data()
                client = socketio.test_client(app, "/test")
                # clear received queue
                client.get_received("/test")

                client.emit("get_code", {"id": "TestID"}, namespace="/test")

                received = client.get_received("/test")

                self.assertEqual(len(received), 2)  # broadcast + confirmation
                self.assertEqual(received[0]['name'], "my_response")
                # TODO self.assertEqual(received[0]['args'][0]["data"], "Someone asked for code")

                self.assertEqual(received[1]['name'], "set_code")

                client.emit("start_code", {"id": "TestID"}, namespace="/test")

                received = client.get_received("/test")

                self.assertEqual(len(received), 1)
                self.assertEqual(received[0]['name'], "my_response")
                # TODO self.assertEqual(received[0]['args'][0]["data"], "Code started")

    def test_get_code(self):
        with app.app_context():
            with self.client:
                self.login_and_upload_data()
                client = socketio.test_client(app, "/test")
                # clear received queue
                client.get_received("/test")

                client.emit("get_code", {"id": "TestID"}, namespace="/test")

                received = client.get_received("/test")
                print(received)

                self.assertEqual(len(received), 2)  # broadcast + confirmation
                self.assertEqual(received[0]['name'], "my_response")
                # TODO self.assertEqual(received[0]['args'][0]["data"], "Someone asked for code")

                self.assertEqual(received[1]['name'], "set_code")

    def test_get_latest_code(self):
        with app.app_context():
            with self.client:
                self.login_and_upload_data()
                client = socketio.test_client(app, "/test")
                # clear received queue
                client.get_received("/test")

                client.emit("get_latest_code", {"id": "TestID"}, namespace="/test")

                received = client.get_received("/test")
                print(received)

                self.assertEqual(len(received), 2)  # broadcast + confirmation
                self.assertEqual(received[0]['name'], "my_response")
                # TODO self.assertEqual(received[0]['args'][0]["data"], "Someone asked for code")

                self.assertEqual(received[1]['name'], "set_code")

    def test_get_code_by_id(self):
        with app.app_context():
            with self.client:
                self.login_and_upload_data()
                client = socketio.test_client(app, "/test")
                # clear received queue
                client.get_received("/test")

                client.emit("get_code_by_id", {"id": "TestID", "task_id": 1}, namespace="/test")

                received = client.get_received("/test")
                print(received)

                self.assertEqual(len(received), 2)  # broadcast + confirmation
                self.assertEqual(received[0]['name'], "my_response")
                # TODO self.assertEqual(received[0]['args'][0]["data"], "Someone asked for code")

                self.assertEqual(received[1]['name'], "set_code")

    def tearDown(self):
        self.delete_data()
        with app.app_context():
            db.drop_all()


class TestAPISockets(BaseTestCase):
    def test_get_code_no_tasks(self):
        client = socketio.test_client(app, "/test")
        # clear received queue
        client.get_received("/test")

        client.emit("get_code", {"id": "TestID"}, namespace="/test")

        received = client.get_received("/test")

        self.assertEqual(len(received), 3)  # broadcast + confirmation
        self.assertEqual(received[0]['name'], "my_response")
        # TODO self.assertEqual(received[0]['args'][0]["data"], "Someone asked for code")
        self.assertEqual(received[1]['name'], "no_tasks")
        self.assertEqual(received[2]['name'], "my_response")

    def test_get_latest_code_no_tasks(self):
        client = socketio.test_client(app, "/test")
        # clear received queue
        client.get_received("/test")

        client.emit("get_latest_code", {"id": "TestID"}, namespace="/test")

        received = client.get_received("/test")

        self.assertEqual(len(received), 3)  # broadcast + confirmation
        self.assertEqual(received[0]['name'], "my_response")
        # TODO self.assertEqual(received[0]['args'][0]["data"], "Someone asked for code")
        self.assertEqual(received[1]['name'], "no_tasks")
        self.assertEqual(received[2]['name'], "my_response")

    def test_get_code_by_id_no_tasks(self):
        client = socketio.test_client(app, "/test")
        # clear received queue
        client.get_received("/test")

        client.emit("get_code_by_id", {"id": "TestID", "task_id": 1}, namespace="/test")

        received = client.get_received("/test")

        self.assertEqual(len(received), 3)  # broadcast + confirmation
        self.assertEqual(received[0]['name'], "my_response")
        # TODO self.assertEqual(received[0]['args'][0]["data"], "Someone asked for code")
        self.assertEqual(received[1]['name'], "no_tasks")
        self.assertEqual(received[2]['name'], "my_response")

    def test_start_code_stop_executing(self):
        client = socketio.test_client(app, "/test")
        # clear received queue
        client.get_received("/test")

        client.emit("start_code", {"id": "TestID"}, namespace="/test")

        received = client.get_received("/test")
        self.assertEqual(len(received), 2)
        self.assertEqual(received[0]['name'], "my_response")
        self.assertEqual(received[1]["name"], "stop_executing")
        self.assertEqual(received[1]["args"], [None])

    def test_execution_failed(self):
        client = socketio.test_client(app, "/test")
        # clear received queue
        client.get_received("/test")

        client.emit("execution_failed",
                    {"id": "TestID", "exception": "you done goofed"},
                    namespace="/test")

        received = client.get_received("/test")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], "my_response")
        # TODO self.assertEqual(received[0]['args'][0]["data"],
        # TODO                  "Client failed executing with stack trace: you done goofed")

    def test_return(self):
        client = socketio.test_client(app, "/test")
        # clear received queue
        client.get_received("/test")

        client.emit("return",
                    {"id": "TestID", "return": "It's bigger on the inside!"},
                    namespace="/test")

        received = client.get_received("/test")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], "my_response")
        # TODO self.assertEqual(received[0]['args'][0]["data"],
        # TODO                  "Client returned following data: It's bigger on the inside!")

    # TODO: reenable error handler
    # def test_bad_return(self):
    #     client = socketio.test_client(app, "/test")
    #     # clear received queue
    #     client.get_received("/test")
    #
    #     client.emit("return", {"id": "TestID"}, namespace="/test")
    #
    #     received = client.get_received("/test")
    #
    #     self.assertEqual(len(received), 1)
    #     self.assertEqual(received[0]['name'], "error")

    def test_get_task_list(self):
        client = socketio.test_client(app, "/test")
        # clear received queue
        client.get_received("/test")

        client.emit("get_task_list", {"id": "TestID"}, namespace="/test")

        received = client.get_received("/test")

        self.assertEqual(len(received), 2)
        self.assertEqual(received[0]['name'], "my_response")
        self.assertEqual(received[1]['name'], "task_list")

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
