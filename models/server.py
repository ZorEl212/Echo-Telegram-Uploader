from models.base_model import BaseModel
from typing import List

class Server(BaseModel):
    userId: str = ""
    serverName: str = ""
    ipAddress: str = ""

    @property
    def availableBuilds(self):
        from models import storage
        return storage.all('Build', 'server_id', self.id)

    def add_user(self, user_id: str):
        if not hasattr(self, 'users'):
            setattr(self, 'users', [user_id])
        if user_id not in self.users:
            self.users.append(user_id)
            return True
        return False
