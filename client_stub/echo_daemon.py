import socketio
import json
import ast
import time
import datetime
from socketio import ClientNamespace
from models.exception.auth import AuthenticationError

sio = socketio.Client(logger=True, engineio_logger=True)

token = None

def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}")
    return wrapper

class DaemonAuthClient(ClientNamespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.token = None  # Load token from secure storage if available

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if callable(attr):
            return exception_handler(attr)
        return attr

    def on_connect(self):
        print(f'Connected to the server on namespace /daemon')
        if not self.token:
            print('No token available, waiting for authentication request')

    def on_connect_error(self, data):
        message = data.get('message')
        error = ast.literal_eval(message)
        err_code = error.get('err_code')
        raise AuthenticationError(error.get('message'), err_code)

    def on_auth_required(self, data):
        print(data['message'])
        # Perform authentication (send userId and serverId)
        user_id = input("User ID: ")
        server_id = input("Server ID: ")
        sio.emit('authenticate', {'userId': user_id, 'serverId': server_id}, namespace='/daemon')

    def on_authenticated(self, data):
        self.token = data['token']
        print(f'Authenticated successfully, received token: {self.token}')
        # Save the token securely for future connections

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
            sio.emit('message', data, namespace='/daemon')
        else:
            print("WebSocket connection is closed, unable to send data.")

sio.register_namespace(DaemonAuthClient('/daemon'))

def send_mock_data():
    # Load mock data
    with open('mock_builds.json') as f:
        mock_builds = json.load(f)

    while True:
        for build in mock_builds:
            DaemonAuthClient.send_build_status(sio, build)
            time.sleep(5)  # Delay to simulate real-time updates

if __name__ == '__main__':
    ws_url = 'http://0.0.0.0:8000'
    sio.connect(ws_url, namespaces=['/daemon'], auth={'token': token} if token else None)
    #send_mock_data()
    sio.wait()
