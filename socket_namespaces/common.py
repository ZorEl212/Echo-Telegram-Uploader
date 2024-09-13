from socketio import Namespace
from models import config, sio
from models.auth import Auth
from socketio.exceptions import ConnectionRefusedError
import threading

def auth_timeout(sid, timeout=15):
    def disconnect():
        session = sio.get_session(sid, namespace='/daemon')
        if not session.get('authenticated', False):
            sio.emit('auth_failed', {'message': 'Authentication timeout', 'err_code': 1005}, to=sid, namespace='/daemon')
            sio.disconnect(sid, namespace='/daemon')
    timer = threading.Timer(timeout, disconnect)
    timer.start()

class Common(Namespace):
    def on_connect(self, sid, environ, auth):
        print(f"Client {sid} connected")
        if auth is None or 'token' not in auth:
            sio.emit('auth_required', {'message': 'Authentication required'}, to=sid, namespace='/daemon')
            auth_timeout(sid)
            return True
        try:
            payload = Auth.verify_token(auth['token'])
            if not payload:
                raise ConnectionRefusedError({'message': 'Invalid token', 'err_code': 1001})
        except Exception as e:
            print(f"Token verification error: {e}")
            raise ConnectionRefusedError({'message': 'Invalid token', 'err_code': 1001})
        session = sio.get_session(sid, namespace='/daemon')
        session['authenticated'] = True
        sio.save_session(sid, session, namespace='/daemon')
        sio.emit('authenticated', {'token': auth['token']}, to=sid, namespace='/daemon')
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
        session = sio.get_session(sid, namespace='/daemon')
        session['authenticated'] = True
        sio.save_session(sid, session, namespace='/daemon')

    def check_auth(self, sid):
        session = sio.get_session(sid, namespace='/daemon')
        return session.get('authenticated', False)

    def on_message(self, sid, data):
        if not self.check_auth(sid):
            self.handle_unauthorized(sid)
            return

        print(f"Received message from {sid}: {data}")

    def handle_unauthorized(self, sid):
        session = sio.get_session(sid, namespace='/daemon')
        session['message_count'] = session.get('message_count', 0) + 1
        sio.save_session(sid, session, namespace='/daemon')

        if not self.check_auth(sid):
            if session['message_count'] >= 3:
                sio.emit('auth_failed', {'message': 'Too many attempts, disconnecting...', 'err_code': 1004}, to=sid, namespace='/daemon')
                sio.disconnect(sid, namespace='/daemon')
            else:
                sio.emit('auth_required', {'message': 'Authentication required'}, to=sid, namespace='/daemon')
                
    def on_disconnect(self, sid):
        print(f"Client {sid} disconnected")
