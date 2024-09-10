#!/usr/bin/env python3

from models.base_model import BaseModel

class Build(BaseModel):
    serverId = ""
    buildName = ""
    buildDir = ""
    buildStatus = ""
    buildLogId = ""