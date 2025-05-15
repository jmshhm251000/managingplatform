import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

username = quote_plus(os.environ['DB_USER'])
password = quote_plus(os.environ['DB_PASS'])

def load_app_config(app, test_config=None):
    app.config.from_mapping(
        SECRET_KEY=os.urandom(24),
        MONGO_URI=f"mongodb+srv://{username}:{password}@hashpartners.xb3vyvi.mongodb.net/sample_mflix?retryWrites=true&w=majority&appName=Hashpartners",
        MONGO_MAX_POOL_SIZE=100,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=3600,
        ACCESS_KEY=os.getenv("ACCESS_KEY"),
        DOCUMENT_ID=os.getenv("DOCUMENT_ID"),
        SCOPES=['https://www.googleapis.com/auth/documents.readonly'],
        VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    )

    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_pyfile('config.py', silent=True)
