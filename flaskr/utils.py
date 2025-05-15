from flask import session, redirect, url_for

def login_required(view_func):
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("gate"))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper