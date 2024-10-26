import socketio
import json
import ast
import threading
import os
import sys
import ast
import datetime
import socket
import configparser
from socketio import ClientNamespace
from models.exception.auth import AuthenticationError
from client_stub.utils import config_loader, config_saver, exception_handler
from engineio.async_drivers import gevent
from models.build import Build

# Global variables
sio = socketio.Client(logger=True, engineio_logger=True)
config = configparser.ConfigParser()
config.add_section('TOKEN')
config.add_section('SERVER')
data_dir = os.path.join(os.getenv('HOME'), '.echo')

class DaemonAuthClient(ClientNamespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.token = ''  # Token to be loaded from secure storage if available
        self.socket_path = '/tmp/echo.sock'

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if callable(attr):
            return exception_handler(attr, verbose=True)
        return attr

    def on_connect_error(self, data):
        message = data.get('message')
        error = ast.literal_eval(message)
        err_code = error.get('err_code')
        raise AuthenticationError(error.get('message'), err_code)

    def on_auth_required(self, data):
        print(data['message'])
        server_info = {}
        # Perform authentication (send userId and serverId)
        if config.has_option('SERVER', 'server'):
            server_info = ast.literal_eval(config.get('SERVER', 'server'))
        user_id = server_info.get('userId', input("User ID: "))
        server_id = server_info.get('id', input("Server ID: "))
        sio.emit('authenticate', {'userId': user_id, 'serverId': server_id}, namespace='/daemon')

    def on_authenticated(self, data):
        self.token = str(data['token'])
        print(f'Authenticated successfully')
        config.set('TOKEN', 'token', self.token)
        if 'server' in data:
            config.set('SERVER', 'server', str(data['server']))
        config_saver(config, data_dir)
        # Start sending mock data after successful authentication
        self.listen_for_build_updates()

    def on_auth_failed(self, data):
        raise AuthenticationError(data['message'], data['err_code'])

    def on_disconnect(self):
        print('Disconnected from the server')

    @classmethod
    def send_build_status(cls, sio, build):
        # Update the timestamp to the current time
        if sio.connected:
            sio.emit('builds_report', build, namespace='/daemon')
        else:
            print("WebSocket connection is closed, unable to send data.")

    def listen_for_build_updates(self):
        print("Listening for build updates")

        def socket_listener():
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.bind(self.socket_path)
                sock.listen()
                while True:
                    conn, _ = sock.accept()
                    thread = threading.Thread(target=handle_client, args=(conn,))
                    thread.start()

        def handle_client(conn):
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    try:
                        command = json.loads(data)
                        server_info = ast.literal_eval(config.get('SERVER', 'server'))
                        # Responding back to the client
                        if command.get('command') == 'add_build':
                            new_build = Build(serverId=server_info.get('id'), buildNmae=command.get('data').get('name'),
                                              buildDir=command.get('data').get('dir'))
                            res = sio.call('add_build', {'server_id': server_info.get('id'), 'build': new_build.to_dict()}, namespace=self.namespace)
                            if res.get('status') == 'success':
                                response = {'success': True, 'data': new_build.to_dict() }
                                conn.send(json.dumps(response).encode('utf-8'))
                        if command.get('command') == 'add_user':
                            res = sio.call('add_user', {'server_id': server_info.get('id'), 'user_id': command.get('user_id')}, namespace=self.namespace)
                            if res.get('status') == 'success':
                                response = {'success': True, 'data': {'user_id': command.get('user_id')}}
                                conn.send(json.dumps(response).encode('utf-8'))
                        else:
                            response = {"status": "received", "build_id": command.get("id")}
                            build_info = {'server_id': server_info.get('id'), 'build_id': command.get('id'), 'data': command.get('data')}
                            conn.send(json.dumps({'status:': 'ok'}).encode('utf-8'))
                            self.send_build_status(sio, build_info)
                    except json.JSONDecodeError:
                        print("Invalid data received")
                        conn.send(b'{"error": "invalid data"}')  # Sending error response

        socket_listener()


def main():
    ws_url = 'http://0.0.0.0:8000'
    global data_dir
    data_dir = os.path.join(data_dir, sys.argv[1])

    print(f"Data directory: {data_dir}")
    try:
        # Load configuration from secure storage
        if os.path.exists(os.path.join(data_dir, 'config.bin')):
            print("Loading configuration from secure storage")
            config.read_dict(config_loader(data_dir))

        # Set up connection with the server
        client = DaemonAuthClient('/daemon')
        sio.register_namespace(client)
        sio.connect(
            ws_url,
            namespaces=['/daemon'],
            auth={'token': config.get('TOKEN', 'token')} if config.has_option('TOKEN', 'token') else None
        )

    except KeyboardInterrupt:
        sio.disconnect()
        config_saver(config, data_dir)
    except Exception as e:
        print(f"Unexpected error: {e}")

    sio.wait()

if __name__ == '__main__':
    print("Starting Echo Daemon client")
    main()
