#!/usr/bin/env python3

from models.base_model import BaseModel

class Server(BaseModel):
    userId = ""
    serverName = ""
    ipAddress = ""
    
    @property
    def availableBuilds(self):
        pass