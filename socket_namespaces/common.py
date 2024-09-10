from socketio import Namespace
from models import config, sio
from models.auth import Auth

class Common(Namespace):
    def on_connect(self, sid, environ, auth):
        print(f"Client {sid} connected")
        if auth is None or 'token' not in auth:
            return {'message': 'Missing token'}
        try:
            payload = Auth.verify_token(auth['token'])
            if not payload:
                return {'message': 'Invalid token'}
        except Exception as e:
            print(f"Token verification error: {e}")
            return {'message': 'Token verification error'}

        return True

    def on_authenticate(self, sid, data):
        userId = data.get('userId')
        serverId = data.get('serverId')

        if not userId or not serverId:
            sio.emit('auth_failed', {'message': 'Missing userId or serverId'}, to=sid)
            print("Missing userId or serverId")
            return {'message': 'Missing userId or serverId'}

        retval = Auth.check_server_details(userId, serverId)
        if not retval:
            return {'message': 'Invalid server details'}

        jwe_data = {'userId': userId, 'serverId': serverId}
        token = Auth.create_token(jwe_data, sid)

        sio.emit('authenticated', {'token': token, 'server': retval}, to=sid)
        return True

    def on_disconnect(self, sid, environ):
        print(f"Client {sid} disconnected")
