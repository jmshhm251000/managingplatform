from flask import Flask, render_template, request, redirect, session, g
from flask_cors import CORS
from .config import load_app_config
from .mongodb import mongo
from .log import logging, LOGGING


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    logging.config.dictConfig(LOGGING)
    load_app_config(app, test_config)

    mongo.init_app(app)

    @app.route('/', methods=["GET", "POST"])
    def gate():
        if session.get("authenticated"):
            return render_template("index.html")
        message = None
        if request.method == "POST":
            user_key = request.form.get("key")
            if user_key == app.config["ACCESS_KEY"]:
                session["authenticated"] = True
                session.permanent = True
                return redirect("/")
            else:
                message = "Incorrect access key. Please try again."

        return render_template("login.html", message=message)
    
    @app.teardown_appcontext
    def teardown_db(exception):
        g.pop('_database', None)

    from .api.db import db_api
    with app.app_context():
        app.register_blueprint(db_api)

    from .api.login import ig_login_api
    app.register_blueprint(ig_login_api)

    from .api.webhooks import webhook_bp
    with app.app_context():
        app.register_blueprint(webhook_bp)

    return app