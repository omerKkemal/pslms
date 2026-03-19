from flask import Flask,request,render_template,Blueprint
from flask_login import login_required

Student = Blueprint('student', __name__,static_folder='static',static_url_path='/static',template_folder='templates')

@Student.route('/student')
@login_required
def index():
    return "Student page"
