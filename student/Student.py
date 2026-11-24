# =========================================================================== #
# Author: Omer Kemal                                                          #
# =========================================================================== #

from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_required
from sqlalchemy.orm import sessionmaker

from database.modle import Student as StudentModel, Assessment, Sections, thought, Subjects, Resource, rank, Parent, SemesterSubjectAverage
from database.manage_db import var, engine
from utility.semester_helpers import get_semesters_and_selected

Student = Blueprint(
    'student', __name__,
    static_folder='static',
    static_url_path='/static',
    template_folder='templates'
)

Session = sessionmaker(bind=engine)


@Student.route('/student')
@Student.route('/student/dashboard')
@login_required
def dashboard():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'student':
            return redirect(url_for('Login.login'))

        student_id = session.get('userID')
        student = _session.query(StudentModel).filter_by(ID=student_id).first()
        if not student:
            return redirect(url_for('Login.login'))

        # Get Student's rank
        student_rank = _session.query(rank).filter_by(student_id=student_id).first()

        # Get Student's subjects from thought table (by grade & section)
        assigned_thoughts = _session.query(thought).filter_by(
            grade=str(student.grade),
            section=student.section
        ).all()

        subject_ids = list(set([t.subject_id for t in assigned_thoughts]))
        subjects = _session.query(Subjects).filter(Subjects.ID.in_(subject_ids)).all() if subject_ids else []

        # Get Subject averages
        semesters, current_semester = get_semesters_and_selected(
            _session, request.args.get('semester_id')
        )
        averages = (
            _session.query(SemesterSubjectAverage)
            .filter_by(student_id=student_id, semester_id=current_semester.ID)
            .all()
            if current_semester else []
        )
        avg_map = {average.subject_id: average.average for average in averages}

        overall_avg = int(sum(avg_map.values()) / len(avg_map)) if avg_map else None

        # Find section ID to lookup resources
        sec = _session.query(Sections).filter_by(grade=student.grade, section=student.section).first()
        sec_id = sec.ID if sec else None
        resources_count = _session.query(Resource).filter_by(section_id=sec_id).count() if sec_id else 0

        # Recent assessments
        recent_assessments = (
            _session.query(Assessment)
            .filter_by(student_id=student_id, semester_id=current_semester.ID)
            .all()
            if current_semester else []
        )

        return render_template(
            'student_dashboard.html',
            student=student,
            rank=student_rank.rank if student_rank else None,
            subjects_count=len(subjects),
            overall_avg=overall_avg,
            resources_count=resources_count,
            recent_assessments=recent_assessments,
            current_semester=current_semester,
            active_page='dashboard'
        )
    except Exception as e:
        var.log(f"Student dashboard error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Student.route('/student/grades')
@login_required
def grades():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'student':
            return redirect(url_for('Login.login'))

        student_id = session.get('userID')
        student = _session.query(StudentModel).filter_by(ID=student_id).first()
        if not student:
            return redirect(url_for('Login.login'))

        # Fetch all assessments for this student
        semesters, selected_semester = get_semesters_and_selected(
            _session, request.args.get('semester_id')
        )
        all_assessments = (
            _session.query(Assessment)
            .filter_by(student_id=student_id, semester_id=selected_semester.ID)
            .all()
            if selected_semester else []
        )

        # Group assessments by subject
        subject_assessments = {}
        for a in all_assessments:
            subj = _session.query(Subjects).filter_by(ID=a.subject_id).first()
            subj_name = subj.subject if subj else a.subject_id
            if subj_name not in subject_assessments:
                subject_assessments[subj_name] = []
            subject_assessments[subj_name].append(a)

        # Averages
        averages = (
            _session.query(SemesterSubjectAverage)
            .filter_by(student_id=student_id, semester_id=selected_semester.ID)
            .all()
            if selected_semester else []
        )
        avg_by_subj = {}
        for avg in averages:
            subj = _session.query(Subjects).filter_by(ID=avg.subject_id).first()
            name = subj.subject if subj else avg.subject_id
            avg_by_subj[name] = avg.average

        # Rank
        r = _session.query(rank).filter_by(student_id=student_id).first()

        return render_template(
            'student_grades.html',
            student=student,
            subject_assessments=subject_assessments,
            averages=avg_by_subj,
            semesters=semesters,
            selected_semester=selected_semester,
            rank=r.rank if r else None,
            active_page='grades'
        )
    except Exception as e:
        var.log(f"Student grades error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Student.route('/student/resources')
@login_required
def resources():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'student':
            return redirect(url_for('Login.login'))

        student_id = session.get('userID')
        student = _session.query(StudentModel).filter_by(ID=student_id).first()
        if not student:
            return redirect(url_for('Login.login'))

        sec = _session.query(Sections).filter_by(grade=student.grade, section=student.section).first()
        if sec:
            resources_list = _session.query(Resource).filter_by(section_id=sec.ID).all()
        else:
            resources_list = []

        return render_template(
            'student_resources.html',
            student=student,
            resources=resources_list,
            active_page='resources'
        )
    except Exception as e:
        var.log(f"Student resources error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Student.route('/student/profile', methods=['GET', 'POST'])
@login_required
def profile():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'student':
            return redirect(url_for('Login.login'))

        student_id = session.get('userID')
        student = _session.query(StudentModel).filter_by(ID=student_id).first()

        if request.method == 'POST':
            old_p = request.form.get('old_password')
            new_p = request.form.get('new_password')
            if old_p == student.password and new_p:
                student.password = new_p
                _session.commit()
                return render_template('student_profile.html', student=student, success="Password updated successfully!", active_page='profile')
            else:
                return render_template('student_profile.html', student=student, error="Current password does not match.", active_page='profile')

        # Parent info
        parents = _session.query(Parent).filter_by(student_id=student_id).all()

        return render_template(
            'student_profile.html',
            student=student,
            parents=parents,
            active_page='profile'
        )
    except Exception as e:
        var.log(f"Student profile error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()
