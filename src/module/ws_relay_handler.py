import json

import tornado.websocket
from tornado.options import define, options


class WsRelayHandler(tornado.websocket.WebSocketHandler):
    clients = dict()
    counter = 0

    def open(self, id_pass):
        self.counter += 1
        relay_id, relay_pass = id_pass.split("-")
        self.clients[self.counter] = {
            "ws": self, "id": relay_id, "password": relay_pass}
        msg = json.dumps({"id": relay_id, "password": relay_pass})
        self.write_message(msg)
        print(msg)

    def on_message(self, message):
        self.clients[self.counter]["ws"].write_message(
            u"You said: %s" % message)
        self.clients[self.counter]["ws"].write_message(
            u"Id: %s" % self.clients[self.counter]["id"])

    def on_close(self):
        print("WebSocket closed")
