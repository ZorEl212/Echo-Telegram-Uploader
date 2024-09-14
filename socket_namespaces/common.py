from socketio import Namespace
from models import sio
from models.auth import Auth
from socketio.exceptions import ConnectionRefusedError
import threading
import resources.strings as strings
import resources.values as values

def auth_timeout(sid, timeout=values.AUTH_TIMEOUT, namespace=None):
    def disconnect():
        session = sio.get_session(sid, namespace=namespace)
        if not session.get('authenticated', False):
            sio.emit('auth_failed', {'message': strings.AUTH_FAILED_TIMEOUT, 'err_code': values.AUTH_ERROR_TIMEOUT}, to=sid, namespace=namespace)
            sio.disconnect(sid, namespace=namespace)
    timer = threading.Timer(timeout, disconnect)
    timer.start()

class Common(Namespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)

    def on_connect(self, sid, environ, auth):
        print(f"Client {sid} {strings.CONNECTED}")
        if auth is None or 'token' not in auth:
            sio.emit('auth_required', {'message': strings.AUTH_REQUIRED}, to=sid, namespace=self.namespace)
            auth_timeout(sid, namespace=self.namespace)
            return True
        try:
            payload = Auth.verify_token(auth['token'])
            if not payload:
                raise ConnectionRefusedError({'message': strings.AUTH_INVALID_TOKEN, 'err_code': values.AUTH_ERROR_INVALID_TOKEN})
        except Exception as e:
            print(f"{strings.EXC_INVALID_TOKEN}: {e}")
            raise ConnectionRefusedError({'message': strings.AUTH_INVALID_TOKEN, 'err_code': values.AUTH_ERROR_INVALID_TOKEN})
        session = sio.get_session(sid, namespace=self.namespace)
        session['authenticated'] = True
        sio.save_session(sid, session, namespace=self.namespace)
        sio.emit('authenticated', {'token': auth['token']}, to=sid, namespace=self.namespace)
        return True

    def on_authenticate(self, sid, data):
        userId = data.get('userId')
        serverId = data.get('serverId')

        if not userId or not serverId:
            sio.emit('auth_failed', {'message': strings.AUTH_MISSING_ID, 'err_code': values.AUTH_ERROR_MISSING_ID}, to=sid, namespace=self.namespace)
            print(strings.AUTH_MISSING_ID)
            sio.disconnect(sid, namespace=self.namespace)

        retval = Auth.check_server_details(userId, serverId)
        if not retval:
            sio.emit('auth_failed', {'message': strings.AUTH_INVALID_DETAILS, 'err_code': values.AUTH_ERROR_INVALID_DETAILS}, to=sid, namespace=self.namespace)
            print("Invalid server details")
            sio.disconnect(sid, namespace=self.namespace)
            return

        jwe_data = {'userId': userId, 'serverId': serverId}
        token = Auth.create_token(jwe_data, sid)
        sio.emit('authenticated', {'token': token, 'server': retval}, to=sid, namespace=self.namespace)
        session = sio.get_session(sid, namespace=self.namespace)
        session['authenticated'] = True
        sio.save_session(sid, session, namespace=self.namespace)

    def check_auth(self, sid):
        session = sio.get_session(sid, namespace=self.namespace)
        return session.get('authenticated', False)

    def on_message(self, sid, data):
        if not self.check_auth(sid):
            self.handle_unauthorized(sid)
            return

        print(f"Received message from {sid}: {data}")

    def handle_unauthorized(self, sid):
        session = sio.get_session(sid, namespace=self.namespace)
        session['message_count'] = session.get('message_count', 0) + 1
        sio.save_session(sid, session, namespace=self.namespace)

        if not self.check_auth(sid):
            if session['message_count'] >= values.MAX_RETRIES:
                sio.emit('auth_failed', {'message': strings.AUTH_MAX_RETRIES_EXCEEDED, 'err_code': values.AUTH_ERROR_MAX_RETRIES}, to=sid, namespace=self.namespace)
                sio.disconnect(sid, namespace=self.namespace)
            else:
                sio.emit('auth_required', {'message': strings.AUTH_REQUIRED}, to=sid, namespace=self.namespace)
                
    def on_disconnect(self, sid):
        print(f"Client {sid} {strings.DISCONNECTED}")
