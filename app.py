# =========================================================================== #
# Author: Omer Kemal                                                          #
# Website: https://www.johndoe.com                                            #
# Social Media:                                                               #
#   - Facebook: https://www.facebook.com/johndoe                              #
#   - Telegram: https://t.me/johndoe                                          #
#   - Twitter: @JohnDoe                                                       #
#   - GitHub: https://github.com/johndoe                                      #
# =========================================================================== #

from flask import Flask
from flask_login import LoginManager, current_user

from admin.Admin import Admin, publish_expired_semesters
from login.login import Login
from student.Student import Student
from teacher.Teacher import Teachters
from parent.Parent import parent as ParentBlueprint
from public.public import public
from event.event import event
from database.manage_db import var, engine, create_grade_reporting_tables

from auth_user import SessionUser

from flask import redirect, request, url_for, session as flask_session


app = Flask(__name__)
var.setting_var()
create_grade_reporting_tables(engine)

app.jinja_env.globals['enumerate'] = enumerate
app.secret_key = var.SECRAT_KEY

# --- Flask-Login setup (protect /admin/*, /student/*, /teacher/*, /parent/*) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'Login.login'

@login_manager.user_loader
def load_user(user_id):
    if str(flask_session.get('userID')) != str(user_id):
        return None

    role = flask_session.get('role')
    username = flask_session.get('username')
    if not role or not username:
        return None

    return SessionUser(flask_session.get('userID'), role, username)


@app.before_request
def require_login_for_protected_prefixes():
    protected_prefixes = ('/admin', '/student', '/teacher', '/parent')
    if request.path.startswith(protected_prefixes):
        if request.path.startswith('/login') or request.path.startswith('/logout'):
            return
        if not current_user.is_authenticated:
            return redirect(url_for('Login.login'))
        publish_expired_semesters()


app.register_blueprint(public)
app.register_blueprint(event)
app.register_blueprint(Teachters)
app.register_blueprint(Admin)
app.register_blueprint(Student)
app.register_blueprint(ParentBlueprint)
app.register_blueprint(Login)


if __name__ == '__main__':
    app.run(debug=True)
