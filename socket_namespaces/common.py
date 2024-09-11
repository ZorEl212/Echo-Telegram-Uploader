from socketio import Namespace
from models import config, sio
from models.auth import Auth
from socketio.exceptions import ConnectionRefusedError
class Common(Namespace):
    def on_connect(self, sid, environ, auth):
        print(f"Client {sid} connected")
        if auth is None or 'token' not in auth:
            sio.emit('auth_required', {'message': 'Authentication required'}, to=sid, namespace='/daemon')
            return True
        try:
            payload = Auth.verify_token(auth['token'])
            if not payload:
                raise ConnectionRefusedError({'message': 'Invalid token', 'err_code': 1001})
        except Exception as e:
            print(f"Token verification error: {e}")
            raise ConnectionRefusedError({'message': 'Invalid token', 'err_code': 1001})

        return True

    def on_authenticate(self, sid, data):
        userId = data.get('userId')
        serverId = data.get('serverId')

        if not userId or not serverId:
            sio.emit('auth_failed', {'message': 'Missing userId or serverId', 'err_code': 1002}, to=sid, namespace='/daemon')
            print("Missing userId or serverId")
            sio.disconnect(sid, namespace='/daemon')

        retval = Auth.check_server_details(userId, serverId)
        if not retval:
            sio.emit('auth_failed', {'message': 'Invalid server details', 'err_code': 1003}, to=sid, namespace='/daemon')
            print("Invalid server details")
            sio.disconnect(sid, namespace='/daemon')
            return

        jwe_data = {'userId': userId, 'serverId': serverId}
        token = Auth.create_token(jwe_data, sid)
        sio.emit('authenticated', {'token': token, 'server': retval}, to=sid, namespace='/daemon')

    def on_disconnect(self, sid):
        print(f"Client {sid} disconnected")
