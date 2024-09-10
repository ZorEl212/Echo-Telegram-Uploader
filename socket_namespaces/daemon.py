from socketio import Namespace
import json
from models.server import Server
from socket_namespaces.common import Common

class Daemon(Common, Namespace):
    def on_auth(self, sid, data):
        server = Server(userId='1234', serverName='Achu Server', ipAddress='192/168.223.56')
        server_info  = {'name': server.serverName, 'token': '12fffeeflpk9r3399jejeoewdd=', 'builds': ['buildid1', 'buildid2', 'buildid3']}
        print(f"Received build data: {data}")
        return server_info