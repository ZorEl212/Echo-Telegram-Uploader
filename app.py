from models import sio
import socketio

from socket_namespaces.daemon import Daemon
from socket_namespaces.common import Common

sio.register_namespace(Common('*'))
sio.register_namespace(Daemon('/daemon'))

app = socketio.WSGIApp(sio, static_files={
    '/': './public/'
})