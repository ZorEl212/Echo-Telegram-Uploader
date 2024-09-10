#!/usr/bin/env python3

from models.base_model import BaseModel
import bcrypt

class User(BaseModel):
    telegram_id = ""
    tgUsername = ""
    fullName = ""
    
