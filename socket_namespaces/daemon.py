from socketio import Namespace
import json
from models.server import Server
from socket_namespaces.common import Common
from models import storage, sio
from models.build import Build
from models.user import User

class Daemon(Common, Namespace):
    def on_builds_report(self, sid, data):
        if not self.check_auth(sid):
            self.handle_unauthorized(sid)
            return
        print(f"Received builds report from {sid}: {data}")
        
    def on_add_build(self, sid, data):
        if not self.check_auth(sid):
            self.handle_unauthorized(sid)
            return
        print(f"Received add build request from {sid}: {data}")
        info = data
        server = storage.get('Server', info.get('server_id'))
        if server:
            build = Build(**info.get('build'))
            print(f"Adding build {build.id} to the database. Dict: {build.to_dict()}")
            storage.new(build)
            return {'status': 'success'}
        else:
            return {'status': 'failed', 'message': 'Server not found'}

    def on_add_user(self, sid, data):
        if not self.check_auth(sid):
            self.handle_unauthorized(sid)
            return
        print(f"Received add user request from {sid}: {data}")
        info = data
        server = storage.get('Server', info.get('server_id'))
        user = storage.get('User', info.get('user_id'))
        if server and user:
            print(f"Adding user {user.id} to server {server.id}")
            server.add_user(user.id)
            storage.update(server)
            print(f'Updated server details: {server.to_dict()}')
            return {'status': 'success'}
        else:
            return {'status': 'failed', 'message': 'Server or user found'}
