# =========================================================================== #
# Author: Omer Kemal                                                          #
# Website: https://www.johndoe.com                                            #
# Social Media:                                                               #
#   - Facebook: https://www.facebook.com/johndoe                              #
#   - Telegram: https://t.me/johndoe                                          #
#   - Twitter: @JohnDoe                                                       #
#   - GitHub: https://github.com/johndoe                                      #
# =========================================================================== #

from flask import render_template, request, Blueprint, session, redirect, url_for,flash
from flask_login import login_user, logout_user

from auth_user import SessionUser
from sqlalchemy.orm import sessionmaker

from database.modle import Student, Teacher, Admin
from database.manage_db import engine, var
from utility.data_processor import read_from_json, write_into_json
from utility._templates_filters import getlist



Session = sessionmaker(bind=engine)
_session = Session()

Login = Blueprint(
    'Login', __name__,
    static_folder=var.STATIC_FOLDE,
    static_url_path=var.STATIC_FOLDE_PATH,
    template_folder=var.TEMPLATE_FOLDER
)

@Login.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            admin = _session.query(Admin).filter(
                Admin.fullname == username,
                Admin.password == password
            ).first()

            teacher = _session.query(Teacher).filter(
                Teacher.fname +" "+Teacher.lname == username,
                Teacher.password == password
            ).first()

            student = _session.query(Student).filter(
                Student.fname+" "+Student.lname == username,
                Student.password == password
            ).first()

            if admin:
                admin = getlist(_session.query(Admin).filter_by(fullname=username,password=password).all())
                session['userID'] = admin[0][0]
                session['role'] = var.ROLES[0]
                session['username'] = username

                # Flask-Login
                user = SessionUser(session['userID'], session['role'], session['username'])
                login_user(user)

                var.log(f'login succsesfully --> {admin}')
                return redirect(url_for('admin.admin'))
            elif student:
                student = getlist(_session.query(Student).filter_by(fname=student[0][0] if False else username,password=password).all())
                # NOTE: your student/teacher branches are currently '...'
                # To keep behavior unchanged, we just redirect to login for now.
                return render_template('login.html')
            elif teacher:
                return render_template('login.html')
            else:
                message = 'Incorrect Username or Password. Try Again...'
                return render_template('login.html')
        else:
            return render_template('login.html')
    except Exception as e:
        var.log(f'Error occurred:--> {e}')
        return redirect(url_for('event.internal_server_error'))

    finally:
        _session.close()
@Login.route('/logout')
def logout():
    if "userID" in session:
        try:
            logout_user()
        except Exception:
            pass

        session.pop("userID", None)
        session.pop("role", None)
        session.pop("username", None)
        return redirect(url_for("Login.login"))

    return redirect(url_for("Login.login"))
