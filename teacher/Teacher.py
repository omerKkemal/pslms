from flask import Flask,request,render_template,Blueprint
from flask_login import login_required

Teachters = Blueprint('teacher', __name__,static_folder='static',static_url_path='/static',template_folder='templates')

@Teachters.route('/teacher')
@login_required
def teacher():
    return "teacher page"
