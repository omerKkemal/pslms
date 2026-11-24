# =========================================================================== #
# Flask-Login compatibility shim for offline/local environments               #
# =========================================================================== #

from functools import wraps
from flask import session, current_app, redirect, url_for, request, g
from werkzeug.local import LocalProxy


class UserMixin:
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(getattr(self, 'id', ''))


class AnonymousUserMixin:
    @property
    def is_active(self):
        return False

    @property
    def is_authenticated(self):
        return False

    @property
    def is_anonymous(self):
        return True

    def get_id(self):
        return None


def _get_user():
    if not hasattr(g, '_login_user'):
        login_manager = current_app.extensions.get('login_manager') if hasattr(current_app, 'extensions') else None
        user_id = session.get('_user_id') or session.get('userID')
        if login_manager and login_manager.user_callback and user_id is not None:
            g._login_user = login_manager.user_callback(user_id)
        else:
            g._login_user = None

    if g._login_user is None:
        return AnonymousUserMixin()
    return g._login_user


current_user = LocalProxy(_get_user)


class LoginManager:
    def __init__(self, app=None):
        self.user_callback = None
        self.login_view = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['login_manager'] = self

    def user_loader(self, callback):
        self.user_callback = callback
        return callback


def login_user(user, remember=False, duration=None, force=False, fresh=True):
    session['_user_id'] = user.get_id()
    g._login_user = user
    return True


def logout_user():
    session.pop('_user_id', None)
    g._login_user = AnonymousUserMixin()
    return True


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            login_manager = current_app.extensions.get('login_manager') if hasattr(current_app, 'extensions') else None
            login_view = login_manager.login_view if login_manager else 'Login.login'
            return redirect(url_for(login_view, next=request.url))
        return func(*args, **kwargs)
    return decorated_view
