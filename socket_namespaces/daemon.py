from socketio import Namespace
import json
from models.server import Server
from socket_namespaces.common import Common

class Daemon(Common, Namespace):
    def on_builds_report(self, sid, data):
        if not self.check_auth(sid):
            self.handle_unauthorized(sid)
            return
        print(f"Received builds report from {sid}: {data}")
