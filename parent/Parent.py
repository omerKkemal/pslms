# =========================================================================== #
# Author: Omer Kemal                                                          #
# =========================================================================== #

from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_required
from sqlalchemy.orm import sessionmaker

from database.modle import Parent as ParentModel, Student, Assessment, Sections, Subjects, Resource, rank, Teacher, ParentGradeAlert, Semester, SemesterSubjectAverage, SemesterGradeReport
from database.manage_db import var, engine
from utility.semester_helpers import get_semesters_and_selected

parent = Blueprint(
    'parent', __name__,
    static_folder='static',
    static_url_path='/static',
    template_folder='templates'
)

Session = sessionmaker(bind=engine)


def _get_parent_children(_session, parent_record):
    children_query = (
        _session.query(Student)
        .join(ParentModel, ParentModel.student_id == Student.ID)
    )

    if parent_record.hous_number and parent_record.hous_number > 0:
        children_query = children_query.filter(
            ParentModel.hous_number == parent_record.hous_number
        )
    else:
        children_query = children_query.filter(ParentModel.ID == parent_record.ID)

    return (
        children_query.distinct()
        .order_by(Student.grade, Student.section, Student.fname, Student.lname)
        .all()
    )


def _selected_child(children):
    requested_id = request.args.get('student_id')
    return (
        next((child for child in children if child.ID == requested_id), None)
        or (children[0] if children else None)
    )


@parent.route('/parent')
@parent.route('/parent/dashboard')
@login_required
def dashboard():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'parent':
            return redirect(url_for('Login.login'))

        parent_id = session.get('userID')
        p = _session.query(ParentModel).filter_by(ID=parent_id).first()
        if not p:
            return redirect(url_for('Login.login'))

        children = _get_parent_children(_session, p)
        semesters, current_semester = get_semesters_and_selected(
            _session, request.args.get('semester_id')
        )
        children_data = []
        for child in children:
            child_rank = _session.query(rank).filter_by(student_id=child.ID).first()
            averages = (
                _session.query(SemesterSubjectAverage)
                .filter_by(student_id=child.ID, semester_id=current_semester.ID)
                .all()
                if current_semester else []
            )
            children_data.append({
                'student': child,
                'rank': child_rank.rank if child_rank else None,
                'overall_avg': (
                    int(sum(average.average for average in averages) / len(averages))
                    if averages else None
                ),
                'recent_assessments': (
                    _session.query(Assessment)
                    .filter_by(student_id=child.ID, semester_id=current_semester.ID)
                    .all()
                    if current_semester else []
                )
            })

        return render_template(
            'parent_dashboard.html',
            parent=p,
            children_data=children_data,
            semesters=semesters,
            current_semester=current_semester,
            active_page='dashboard'
        )
    except Exception as e:
        var.log(f"Parent dashboard error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@parent.route('/parent/grades')
@login_required
def grades():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'parent':
            return redirect(url_for('Login.login'))

        parent_id = session.get('userID')
        p = _session.query(ParentModel).filter_by(ID=parent_id).first()
        if not p:
            return redirect(url_for('Login.login'))

        children = _get_parent_children(_session, p)
        student = _selected_child(children)
        semesters, selected_semester = get_semesters_and_selected(
            _session, request.args.get('semester_id')
        )
        if not student:
            return render_template(
                'parent_grades.html',
                parent=p,
                children=children,
                student=None,
                subject_assessments={},
                averages={},
                semesters=semesters,
                selected_semester=selected_semester,
                rank=None,
                active_page='grades'
            )

        # Assessments
        all_assessments = (
            _session.query(Assessment)
            .filter_by(student_id=student.ID, semester_id=selected_semester.ID)
            .all()
            if selected_semester else []
        )
        subject_assessments = {}
        for a in all_assessments:
            subj = _session.query(Subjects).filter_by(ID=a.subject_id).first()
            sname = subj.subject if subj else a.subject_id
            if sname not in subject_assessments:
                subject_assessments[sname] = []
            subject_assessments[sname].append(a)

        # Subject averages
        averages = (
            _session.query(SemesterSubjectAverage)
            .filter_by(student_id=student.ID, semester_id=selected_semester.ID)
            .all()
            if selected_semester else []
        )
        avg_by_subj = {}
        for avg in averages:
            subj = _session.query(Subjects).filter_by(ID=avg.subject_id).first()
            sname = subj.subject if subj else avg.subject_id
            avg_by_subj[sname] = avg.average

        r = _session.query(rank).filter_by(student_id=student.ID).first()

        return render_template(
            'parent_grades.html',
            parent=p,
            children=children,
            student=student,
            subject_assessments=subject_assessments,
            averages=avg_by_subj,
            semesters=semesters,
            selected_semester=selected_semester,
            rank=r.rank if r else None,
            active_page='grades'
        )
    except Exception as e:
        var.log(f"Parent grades error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@parent.route('/parent/alerts')
@login_required
def alerts():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'parent':
            return redirect(url_for('Login.login'))

        parent_record = _session.query(ParentModel).filter_by(ID=session.get('userID')).first()
        if not parent_record:
            return redirect(url_for('Login.login'))

        alerts_list = (
            _session.query(ParentGradeAlert)
            .filter_by(parent_id=parent_record.ID)
            .order_by(ParentGradeAlert.created_at.desc(), ParentGradeAlert.ID.desc())
            .all()
        )
        attention_counts = {}
        for alert in alerts_list:
            if alert.alert_type == 'attention':
                key = (alert.student_id, alert.subject_id, alert.semester_id)
                attention_counts[key] = attention_counts.get(key, 0) + 1

        alert_rows = []
        for alert in alerts_list:
            child = _session.query(Student).filter_by(ID=alert.student_id).first()
            subject = _session.query(Subjects).filter_by(ID=alert.subject_id).first()
            semester = (
                _session.query(Semester).filter_by(ID=alert.semester_id).first()
                if alert.semester_id else None
            )
            alert_rows.append({
                'alert': alert,
                'student_name': f'{child.fname} {child.lname}' if child else alert.student_id,
                'subject_name': subject.subject if subject else alert.subject_id,
                'semester_name': semester.name if semester else None,
                'attention_count': attention_counts.get(
                    (alert.student_id, alert.subject_id, alert.semester_id), 0
                )
            })

        return render_template(
            'parent_alerts.html',
            parent=parent_record,
            alert_rows=alert_rows,
            active_page='alerts'
        )
    except Exception as e:
        var.log(f"Parent alerts error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@parent.route('/parent/reports')
@login_required
def reports():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'parent':
            return redirect(url_for('Login.login'))

        parent_record = _session.query(ParentModel).filter_by(ID=session.get('userID')).first()
        if not parent_record:
            return redirect(url_for('Login.login'))

        children = _get_parent_children(_session, parent_record)
        child_ids = [child.ID for child in children]
        student = _selected_child(children)
        report_rows = []
        if child_ids:
            query = (
                _session.query(SemesterGradeReport, Semester, Student, Subjects)
                .join(Semester, Semester.ID == SemesterGradeReport.semester_id)
                .join(Student, Student.ID == SemesterGradeReport.student_id)
                .join(Subjects, Subjects.ID == SemesterGradeReport.subject_id)
                .filter(
                    SemesterGradeReport.student_id.in_(child_ids),
                    Semester.closed_at.isnot(None)
                )
            )
            if student:
                query = query.filter(SemesterGradeReport.student_id == student.ID)
            rows = query.order_by(
                Semester.closed_at.desc(),
                Student.fname,
                Subjects.subject
            ).all()
            report_rows = [
                {'report': report, 'semester': semester, 'student': child, 'subject': subject}
                for report, semester, child, subject in rows
            ]

        return render_template(
            'parent_reports.html',
            parent=parent_record,
            children=children,
            student=student,
            report_rows=report_rows,
            active_page='reports'
        )
    except Exception as e:
        var.log(f"Parent semester reports error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@parent.route('/parent/resources')
@login_required
def resources():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'parent':
            return redirect(url_for('Login.login'))

        parent_id = session.get('userID')
        p = _session.query(ParentModel).filter_by(ID=parent_id).first()
        if not p:
            return redirect(url_for('Login.login'))

        children = _get_parent_children(_session, p)
        student = _selected_child(children)
        resources_list = []
        if student:
            sec = _session.query(Sections).filter_by(grade=student.grade, section=student.section).first()
            if sec:
                resources_list = _session.query(Resource).filter_by(section_id=sec.ID).all()

        return render_template(
            'parent_resources.html',
            parent=p,
            children=children,
            student=student,
            resources=resources_list,
            active_page='resources'
        )
    except Exception as e:
        var.log(f"Parent resources error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@parent.route('/parent/profile', methods=['GET', 'POST'])
@login_required
def profile():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'parent':
            return redirect(url_for('Login.login'))

        parent_id = session.get('userID')
        p = _session.query(ParentModel).filter_by(ID=parent_id).first()
        if not p:
            return redirect(url_for('Login.login'))

        if request.method == 'POST':
            old_p = request.form.get('old_password')
            new_p = request.form.get('new_password')
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()

            if email:
                p.email = email
            if phone:
                p.phone = phone

            if old_p and new_p:
                if old_p == p.password:
                    p.password = new_p
                    _session.commit()
                    return render_template(
                        'parent_profile.html',
                        parent=p,
                        children=_get_parent_children(_session, p),
                        success="Profile & Password updated successfully!",
                        active_page='profile'
                    )
                else:
                    return render_template(
                        'parent_profile.html',
                        parent=p,
                        children=_get_parent_children(_session, p),
                        error="Current password does not match.",
                        active_page='profile'
                    )

            _session.commit()
            return render_template(
                'parent_profile.html',
                parent=p,
                children=_get_parent_children(_session, p),
                success="Contact information updated!",
                active_page='profile'
            )

        return render_template(
            'parent_profile.html',
            parent=p,
            children=_get_parent_children(_session, p),
            active_page='profile'
        )
    except Exception as e:
        var.log(f"Parent profile error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()
