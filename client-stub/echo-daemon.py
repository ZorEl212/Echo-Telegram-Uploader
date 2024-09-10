import socketio
import json
import time
import datetime
from socketio import ClientNamespace

sio = socketio.Client()

token = None
class DaemonAuthClient(ClientNamespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.token = None  # Load token from secure storage if available

    def on_connect(self):
        print(f'Connected to the server on namespace /daemon')
        if not self.token:
            print('No token available, waiting for authentication request')
           # userId = input("User ID: ")
           # serverId = input("Server ID: ")
           # sio.call('authenticate', {'userId': userId, 'serverId': serverId}, namespace='/daemon')

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
        print(f'Authentication failed: {data["message"]}')
        return None

    def on_disconnect(self):
        print('Disconnected from the server')

    def connect(self, url):
        # Connect to the server, sending token if available
        headers = {'Authorization': f'Bearer {self.token}'}
        sio.connect(url, headers=headers, namespaces=['/daemon'])

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
    ws_url = 'http://localhost:8000'
    sio.connect(ws_url, namespaces=['/daemon'], auth={'token': token} if token else None)
    send_mock_data()
    sio.wait()
