#!/usr/bin/env python3

from models.base_model import BaseModel

class Server(BaseModel):
    userId = ""
    serverName = ""
    ipAddress = ""
    server_users = set()
    
    @property
    def availableBuilds(self):
        from models import storage
        return storage.all('Build', 'server_id', self.id)

    def add_user(self, userId):
        if userId not in self.server_users:
            self.server_users.add(userId)
            return True
        return False
