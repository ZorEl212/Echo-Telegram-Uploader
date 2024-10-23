#!/usr/bin/env python3

from uuid import uuid4
from datetime import datetime
import redis


class BaseModel:
    def __init__(self, **kwargs) -> None:
        self.id = str(uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        for key, value in kwargs.items():
            if key in ['created_at', 'updated_at']:
                value = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f')
            if key != 'cls_name':    
                setattr(self, key, value)

    @classmethod
    def get_cls_name(cls):
        return cls.__name__

    @property
    def cls_name(self):
        return self.get_cls_name()
    
    def __str__(self):
        return f"[{self.cls_name}] ({self.id}) {self.__dict__}"

    def to_dict(self):
        new_dict = vars(self).copy()
        for key, value in list(new_dict.items()):
            if isinstance(value, datetime):
                new_dict[key] = value.strftime('%Y-%m-%dT%H:%M:%S.%f')
        new_dict['cls_name'] = self.cls_name 
        return new_dict