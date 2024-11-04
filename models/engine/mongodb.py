#!/usr/bin/env python3

from pymongo import MongoClient
from models.build import Build
from models.files import LogFile, OutFile
from models.server import Server
from models.user import User

class DBClient:
    classes = [Build, User, Server, LogFile, OutFile]
    
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017')
        self.database = self.client['echo_monitor_db']

    def all(self, cls=None, attr=None, value=None):
        docs = {}

        def process_collection(collection):
            query = {attr: value} if cls and attr and value else {}
            for document in collection.find(query):
                key = f"{document['cls_name']}.{document['id']}"
                document.pop('_id', None)
                docs[key] = document

        if cls:
            collection = self.database[cls if isinstance(cls, str) else cls.get_cls_name()]
            process_collection(collection)
        else:
            for cls in self.classes:
                collection = self.database[cls.get_cls_name()]
                process_collection(collection)

        return docs if len(docs) > 0 else None

    def new(self, obj):
        collection = self.database[obj.cls_name]
        collection.insert_one(obj.to_dict())

    def delete(self, obj):
        collection = self.database[obj.cls_name]
        collection.delete_one({'id': obj.id})

    def get(self, cls, id):
        if cls is None:
            return None
        if isinstance(cls, str):
            cls = next((c for c in self.classes if c.get_cls_name() == cls), None)

        collection = self.database[cls.get_cls_name()]
        document = collection.find_one({'id': id})

        if document is not None:
            document.pop('_id')  
            document.pop('cls_name')
            return cls(**document)

        return None  # Return None if document is not found

    def get_by_attr(self, cls, attr, value):
        if cls is None:
            return None
        if isinstance(cls, str):
            cls = next((c for c in self.classes if c.get_cls_name() == cls), None)

        collection = self.database[cls.get_cls_name()]
        document = collection.find_one({attr: value})

        if document is not None:
            document.pop('_id')
            document.pop('cls_name')
            return cls(**document)

        return None
    
    def update(self, obj):
        collection = self.database[obj.cls_name]
        collection.update_one({'id': obj.id}, {'$set': obj.to_dict()})
        return obj

    def update_attrib(self, obj, attr, value):
        collection = self.database[obj.cls_name]
        result = collection.update_one({'id': obj.id}, {'$set': {attr: value}})
        return True if result.modified_count > 0 else False
        
    def close(self):
        self.client.close()

    def count(self, cls=None):
        if cls is None:
            return self.database.command("dbstats")['objects']
        elif isinstance(cls, str):
            collection = self.database[cls]
        elif hasattr(cls, 'get_cls_name'):
            collection = self.database[cls.get_cls_name()]
        return collection.count_documents({})
