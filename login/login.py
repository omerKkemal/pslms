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



from flask import render_template, request, Blueprint, session, redirect, url_for, flash
from flask_login import login_user, logout_user

from auth_user import SessionUser
from sqlalchemy.orm import sessionmaker

from database.modle import Student, Teacher, Admin, Parent
from database.manage_db import engine, var
from utility.data_processor import read_from_json, write_into_json
from utility._templates_filters import getlist



Session = sessionmaker(bind=engine)

Login = Blueprint(
    'Login', __name__,
    static_folder=var.STATIC_FOLDE,
    static_url_path=var.STATIC_FOLDE_PATH,
    template_folder=var.TEMPLATE_FOLDER
)

@Login.route('/login', methods=['GET', 'POST'])
def login():
    _session = Session()
    try:
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            # 1. Check Admin (by fullname or ID)
            admin = _session.query(Admin).filter(
                (Admin.fullname == username) | (Admin.ID == username),
                Admin.password == password
            ).first()

            if admin:
                session['userID'] = admin.ID
                session['role'] = 'admin'
                session['username'] = admin.fullname

                user = SessionUser(session['userID'], session['role'], session['username'])
                login_user(user)
                var.log(f'Admin logged in: {admin.fullname}')
                return redirect(url_for('admin.dashboard'))

            # 2. Check Teacher (by full name, first+last, first+middle, fname, or ID)
            teacher = _session.query(Teacher).filter(
                (
                    (Teacher.fname + " " + Teacher.lname == username) |
                    (Teacher.fname + " " + Teacher.mname + " " + Teacher.lname == username) |
                    (Teacher.fname + " " + Teacher.mname == username) |
                    (Teacher.fname == username) |
                    (Teacher.ID == username)
                ),
                Teacher.password == password
            ).first()

            if teacher:
                session['userID'] = teacher.ID
                session['role'] = 'teacher'
                session['username'] = f"{teacher.fname} {teacher.lname}"

                user = SessionUser(session['userID'], session['role'], session['username'])
                login_user(user)
                var.log(f'Teacher logged in: {teacher.fname} {teacher.lname}')
                return redirect(url_for('teacher.dashboard'))

            # 3. Check Student (by "fname lname", "fname", or ID)
            student = _session.query(Student).filter(
                (
                    (Student.fname + " " + Student.lname == username) |
                    (Student.fname == username) |
                    (Student.ID == username)
                ),
                Student.password == password
            ).first()

            if student:
                session['userID'] = student.ID
                session['role'] = 'student'
                session['username'] = f"{student.fname} {student.lname}"

                user = SessionUser(session['userID'], session['role'], session['username'])
                login_user(user)
                var.log(f'Student logged in: {student.fname} {student.lname}')
                return redirect(url_for('student.dashboard'))

            # 4. Check Parent (by "fname lname", email, phone, or ID)
            parent = _session.query(Parent).filter(
                (
                    (Parent.fname + " " + Parent.lname == username) |
                    (Parent.fname == username) |
                    (Parent.email == username) |
                    (Parent.phone == username) |
                    (Parent.ID == username)
                ),
                Parent.password == password
            ).first()

            if parent:
                session['userID'] = parent.ID
                session['role'] = 'parent'
                session['username'] = f"{parent.fname} {parent.lname}"

                user = SessionUser(session['userID'], session['role'], session['username'])
                login_user(user)
                var.log(f'Parent logged in: {parent.fname} {parent.lname}')
                return redirect(url_for('parent.dashboard'))

            # If invalid credentials
            error_message = 'Incorrect Username or Password. Please try again.'
            return render_template('login.html', error=error_message)
        else:
            return render_template('login.html')
    except Exception as e:
        var.log(f'Error occurred in login: {e}')
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
