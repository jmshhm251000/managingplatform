from flask import g, current_app
from flask_pymongo import PyMongo
from werkzeug.local import LocalProxy


mongo = PyMongo()

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = mongo.db
    return db

db = LocalProxy(get_db)