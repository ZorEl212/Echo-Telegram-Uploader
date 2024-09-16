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
        build['timestamp'] = datetime.datetime.utcnow().isoformat() + 'Z'
        data = json.dumps(build)
        if sio.connected:
            sio.emit('builds_report', data, namespace='/daemon')
        else:
            print("WebSocket connection is closed, unable to send data.")

    def listen_for_build_updates(self):
        print("Listening for build updates")
        def socket_listner():
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
                    if data:
                        build = json.loads(data)
                        self.send_build_status(sio, build)
            
        socket_listner()

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
