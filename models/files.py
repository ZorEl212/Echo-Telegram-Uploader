#!/usr/bin/env python3

from models.base_model import BaseModel

class OutFile(BaseModel):
    fileName = ""
    buildId = ""
    filePath = ""
    fileSize = ""
    telegramUrl = ""


class LogFile(BaseModel):
    fileName = ""
    buildId = ""
    pastebinUrl = ""
    telegramUrl = ""
    
    
    