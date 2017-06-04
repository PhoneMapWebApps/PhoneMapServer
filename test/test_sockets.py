import unittest

from app import create_app, app, db, socketio


class TestSockets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(False, True)

    def test_connect(self):
        client = socketio.test_client(app, "/test")
        received = client.get_received("/test")
        assert len(received) == 1
        assert received[0]["args"][0]["data"] == "Connected"
        client.disconnect("/test")

    def test_disconnect_reconnect(self):
        client = socketio.test_client(app, "/test")
        # clear received queue
        client.get_received("/test")
        # reconnect
        client.disconnect("/test")
        client.connect("/test")
        received = client.get_received("/test")
        print(received)
        assert len(received) == 1
        assert received[0]["args"][0]["data"] == "Connected"

        client.emit("my_event", {"data": "junk"}, namespace="/test")
        snd_received = client.get_received("/test")
        print(snd_received)
        assert len(snd_received) == 1
        assert len(snd_received[0]["args"]) == 1
        assert snd_received[0]["args"][0]["data"] == "junk"
        client.disconnect("/test")

    def test_emit(self):
        client = socketio.test_client(app, "/test")
        client.get_received("/test")
        client.emit("my_event", {"data": "this is good data"}, namespace="/test")
        received = client.get_received("/test")

        assert len(received) == 1
        assert len(received[0]["args"])
        assert received[0]["name"] == "my_response"
        assert received[0]["args"][0]["data"] == "this is good data"

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

        assert not client3.get_received()
        assert len(received_1) == 1
        assert len(received_2) == 1
        assert received_1[0]['name'] == "my_response"
        assert received_1[0]["args"][0]["data"] == "42"
        assert received_2[0]['name'] == "my_response"
        assert received_2[0]["args"][0]["data"] == "42"

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
