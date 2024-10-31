#!/usr/bin/env python3

from models.base_model import BaseModel

class Build(BaseModel):
    serverId = ""
    userId = ""
    buildName = ""
    buildDir = ""
    buildStatus = ""
    buildLogId = ""