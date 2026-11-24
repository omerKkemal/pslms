# =========================================================================== #
# Author: Omer Kemal                                                          #
# =========================================================================== #

import os
from datetime import date
from flask import Flask, request, render_template, Blueprint, session, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

from database.modle import Student, Teacher, Parent, ParentGradeAlert, CreatAssessment, Assessment, Sections, thought, Subjects, Resource, avrage, rank, totalAssessment, Semester, SemesterSubjectAverage
from database.manage_db import var, engine
from utility.data_processor import allowed_file

Teachters = Blueprint(
    'teacher', __name__,
    static_folder='static',
    static_url_path='/static',
    template_folder='templates'
)

Session = sessionmaker(bind=engine)


def _calculate_subject_average(_session, student_id, subject_id, semester_id=None):
    query = _session.query(Assessment).filter_by(
        student_id=student_id,
        subject_id=subject_id
    )
    if semester_id is not None:
        query = query.filter_by(semester_id=semester_id)
    assessments = query.all()
    if not assessments:
        return None

    total_score = 0.0
    total_possible = 0.0
    for assessment in assessments:
        definition = _session.query(CreatAssessment).filter_by(
            Assessment_of=assessment.teacher_id,
            Assessment_name=assessment.AssessmentName
        ).first()
        max_mark = (
            float(definition.Mark)
            if definition and definition.Mark and definition.Mark > 0
            else 100.0
        )
        total_score += float(assessment.ScoreMark)
        total_possible += max_mark

    if total_possible == 0:
        return None
    return int(round(total_score / total_possible * 100))


def _update_subject_average(_session, student_id, subject_id):
    average_value = _calculate_subject_average(_session, student_id, subject_id)
    if average_value is None:
        return

    average_entry = _session.query(avrage).filter_by(
        student_id=student_id,
        Subjects=subject_id
    ).first()
    if average_entry:
        average_entry.avrage = average_value
    else:
        average_entry = avrage(
            ID=var.ID(),
            student_id=student_id,
            avrage=average_value,
            simister=1.0
        )
        average_entry.Subjects = subject_id
        _session.add(average_entry)


def _update_semester_subject_average(_session, student_id, subject_id, semester_id):
    average_value = _calculate_subject_average(
        _session, student_id, subject_id, semester_id
    )
    if average_value is None:
        return

    average_entry = _session.query(SemesterSubjectAverage).filter_by(
        student_id=student_id,
        subject_id=subject_id,
        semester_id=semester_id
    ).first()
    if average_entry:
        average_entry.average = average_value
    else:
        _session.add(SemesterSubjectAverage(
            ID=var.ID(),
            student_id=student_id,
            subject_id=subject_id,
            semester_id=semester_id,
            average=average_value
        ))


def _get_active_semester(_session):
    today = date.today()
    return _session.query(Semester).filter(
        Semester.starts_on <= today,
        Semester.ends_on >= today,
        Semester.closed_at.is_(None)
    ).order_by(Semester.starts_on.desc()).first()


def _notify_parents_of_grade_change(
    _session, student_id, subject_id, semester_id, previous_average, average
):
    if average < 50:
        alert_type = 'attention'
    elif previous_average is not None and average > previous_average:
        alert_type = 'improvement'
    else:
        return

    parents = _session.query(Parent).filter_by(student_id=student_id).all()
    household_numbers = {
        parent.hous_number for parent in parents
        if parent.hous_number and parent.hous_number > 0
    }
    if household_numbers:
        household_parents = _session.query(Parent).filter(
            Parent.hous_number.in_(household_numbers)
        ).all()
        parent_ids = {parent.ID for parent in parents}
        parents.extend(parent for parent in household_parents if parent.ID not in parent_ids)

    event_id = var.ID()
    for parent in parents:
        _session.add(ParentGradeAlert(
            ID=var.ID(),
            parent_id=parent.ID,
            student_id=student_id,
            subject_id=subject_id,
            semester_id=semester_id,
            event_id=event_id,
            alert_type=alert_type,
            average=average,
            previous_average=previous_average
        ))


@Teachters.route('/teacher')
@Teachters.route('/teacher/dashboard')
@login_required
def dashboard():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'teacher':
            return redirect(url_for('Login.login'))

        teacher_id = session.get('userID')
        teacher = _session.query(Teacher).filter_by(ID=teacher_id).first()

        # Assigned classes & subjects (exclude Forbidden access)
        assignments = _session.query(thought).filter(
            thought.teacher_id == teacher_id,
            thought.access_level != 'Forbidden'
        ).all()
        assigned_list = []
        for a in assignments:
            subj = _session.query(Subjects).filter_by(ID=a.subject_id).first()
            subj_name = subj.subject if subj else a.subject_id
            assigned_list.append({
                'id': a.ID,
                'subject_id': a.subject_id,
                'subject_name': subj_name,
                'grade': a.grade,
                'section': a.section,
                'access_level': a.access_level
            })

        # Count assessments created by teacher
        my_assessments_count = _session.query(CreatAssessment).filter_by(Assessment_of=teacher_id).count()

        # Count uploaded resources
        my_resources_count = _session.query(Resource).filter_by(post_t=teacher_id).count()

        return render_template(
            'teacher_dashboard.html',
            teacher=teacher,
            assignments=assigned_list,
            assessments_count=my_assessments_count,
            resources_count=my_resources_count,
            active_page='dashboard'
        )
    except Exception as e:
        var.log(f"Teacher dashboard error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Teachters.route('/teacher/classes')
@login_required
def my_classes():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'teacher':
            return redirect(url_for('Login.login'))

        teacher_id = session.get('userID')
        assignments = _session.query(thought).filter(
            thought.teacher_id == teacher_id,
            thought.access_level != 'Forbidden'
        ).all()
        classes = []
        for a in assignments:
            subj = _session.query(Subjects).filter_by(ID=a.subject_id).first()
            student_count = _session.query(Student).filter_by(grade=int(a.grade), section=a.section).count()
            classes.append({
                'assignment_id': a.ID,
                'subject_id': a.subject_id,
                'subject_name': subj.subject if subj else a.subject_id,
                'grade': a.grade,
                'section': a.section,
                'access_level': a.access_level,
                'student_count': student_count
            })

        return render_template('teacher_classes.html', classes=classes, active_page='classes')
    except Exception as e:
        var.log(f"Teacher classes error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Teachters.route('/teacher/class/<grade>/<section>/<subject_id>')
@login_required
def class_students(grade, section, subject_id):
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'teacher':
            return redirect(url_for('Login.login'))

        teacher_id = session.get('userID')
        # verify assignment (and check not forbidden)
        assigned = _session.query(thought).filter_by(
            teacher_id=teacher_id, grade=str(grade), section=section, subject_id=subject_id
        ).first()

        if not assigned or assigned.access_level == 'Forbidden':
            return redirect(url_for('teacher.my_classes'))

        subject = _session.query(Subjects).filter_by(ID=subject_id).first()
        subj_name = subject.subject if subject else subject_id
        semester = _get_active_semester(_session)

        students = _session.query(Student).filter_by(grade=int(grade), section=section).all()

        # Get existing assessments for this teacher and subject/class
        assessments_query = _session.query(Assessment).filter_by(
            teacher_id=teacher_id,
            grade=str(grade),
            section=section,
            subject_id=subject_id
        )
        if semester:
            assessments_query = assessments_query.filter_by(semester_id=semester.ID)
        else:
            assessments_query = assessments_query.filter(Assessment.ID == '')
        assessments = assessments_query.all()

        # Build map: student_id -> list of assessment records
        student_assessments = {}
        for s in students:
            student_assessments[s.ID] = []

        for ass in assessments:
            if ass.student_id in student_assessments:
                student_assessments[ass.student_id].append(ass)

        # Also get assessment definitions by this teacher
        created_assessments = _session.query(CreatAssessment).filter_by(Assessment_of=teacher_id).all()

        return render_template(
            'class_students.html',
            grade=grade,
            section=section,
            subject_id=subject_id,
            subject_name=subj_name,
            semester=semester,
            students=students,
            student_assessments=student_assessments,
            created_assessments=created_assessments,
            access_level=assigned.access_level if assigned else 'Read&Write'
        )
    except Exception as e:
        var.log(f"Class students error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Teachters.route('/teacher/assessment/create', methods=['GET', 'POST'])
@login_required
def create_assessment():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'teacher':
            return redirect(url_for('Login.login'))

        teacher_id = session.get('userID')

        if request.method == 'POST':
            name = request.form.get('assessment_name', '').strip()
            mark = float(request.form.get('mark', 0))

            if name and mark > 0:
                item = CreatAssessment(
                    ID=var.ID(),
                    Assessment_name=name,
                    Assessment_of=teacher_id,
                    Mark=mark
                )
                _session.add(item)
                _session.commit()
                return redirect(url_for('teacher.create_assessment'))

        # List existing assessment types created by this teacher
        items = _session.query(CreatAssessment).filter_by(Assessment_of=teacher_id).all()
        return render_template('teacher_create_assessment.html', items=items, active_page='assessments')
    except Exception as e:
        _session.rollback()
        var.log(f"Create assessment error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Teachters.route('/teacher/grade/submit', methods=['POST'])
@login_required
def submit_grades():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'teacher':
            return redirect(url_for('Login.login'))

        teacher_id = session.get('userID')
        student_id = request.form.get('student_id')
        subject_id = request.form.get('subject_id')
        grade = request.form.get('grade')
        section = request.form.get('section')
        assessment_name = request.form.get('assessment_name', '').strip()
        class_url = url_for(
            'teacher.class_students',
            grade=grade,
            section=section,
            subject_id=subject_id
        )

        semester = _get_active_semester(_session)
        if not semester:
            flash('No active semester. Ask an administrator to set the semester dates.', 'error')
            return redirect(class_url)

        if not assessment_name:
            flash('Enter an assessment name before saving the grade.', 'error')
            return redirect(class_url)

        try:
            score = float(request.form.get('score', ''))
        except (TypeError, ValueError):
            flash('Enter a valid numeric score.', 'error')
            return redirect(class_url)

        assessment_definition = _session.query(CreatAssessment).filter_by(
            Assessment_of=teacher_id,
            Assessment_name=assessment_name
        ).first()
        max_mark = (
            float(assessment_definition.Mark)
            if assessment_definition and assessment_definition.Mark
            else 100.0
        )
        if not 0 <= score <= max_mark:
            flash(f'Score must be between 0 and {max_mark:g} for this assessment.', 'error')
            return redirect(class_url)

        # Check if record already exists
        existing = _session.query(Assessment).filter_by(
            student_id=student_id,
            teacher_id=teacher_id,
            subject_id=subject_id,
            grade=str(grade),
            section=section,
            AssessmentName=assessment_name,
            semester_id=semester.ID
        ).first()

        grade_changed = existing is None or existing.ScoreMark != score
        previous_average = (
            _calculate_subject_average(
                _session, student_id, subject_id, semester.ID
            )
            if grade_changed else None
        )

        if existing:
            existing.ScoreMark = score
        else:
            rec = Assessment(
                ID=var.ID(),
                student_id=student_id,
                teacher_id=teacher_id,
                subject_id=subject_id,
                grade=str(grade),
                section=section,
                AssessmentName=assessment_name,
                ScoreMark=score,
                semester_id=semester.ID
            )
            _session.add(rec)

        _update_subject_average(_session, student_id, subject_id)
        _update_semester_subject_average(
            _session, student_id, subject_id, semester.ID
        )
        if grade_changed:
            current_average = _calculate_subject_average(
                _session, student_id, subject_id, semester.ID
            )
            if current_average is not None:
                _notify_parents_of_grade_change(
                    _session, student_id, subject_id, semester.ID,
                    previous_average, current_average
                )
        _session.commit()

        return redirect(url_for('teacher.class_students', grade=grade, section=section, subject_id=subject_id))
    except Exception as e:
        _session.rollback()
        var.log(f"Grade submit error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Teachters.route('/teacher/calculate_ranks/<grade>/<section>')
@login_required
def calculate_ranks(grade, section):
    """Computes ranks for all students in this grade and section based on average marks."""
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'teacher':
            return redirect(url_for('Login.login'))

        students = _session.query(Student).filter_by(grade=int(grade), section=section).all()
        student_ids = [student.ID for student in students]
        student_subjects = (
            _session.query(Assessment.student_id, Assessment.subject_id)
            .filter(Assessment.student_id.in_(student_ids))
            .distinct()
            .all()
            if student_ids else []
        )
        for student_id, subject_id in student_subjects:
            _update_subject_average(_session, student_id, subject_id)

        student_scores = []
        for s in students:
            # sum of averages across subjects
            avgs = _session.query(avrage.avrage).filter_by(student_id=s.ID).all()
            total_avg = sum([a[0] for a in avgs]) if avgs else 0
            student_scores.append((s.ID, total_avg))

        # sort descending by total_avg
        student_scores.sort(key=lambda x: x[1], reverse=True)

        # Update rank table
        for r_idx, (s_id, _) in enumerate(student_scores, 1):
            r_entry = _session.query(rank).filter_by(student_id=s_id).first()
            if r_entry:
                r_entry.rank = r_idx
            else:
                r_entry = rank(
                    ID=var.ID(),
                    student_id=s_id,
                    rank=r_idx,
                    simister=1.0
                )
                _session.add(r_entry)

        _session.commit()
        return redirect(url_for('teacher.my_classes'))
    except Exception as e:
        _session.rollback()
        var.log(f"Calculate ranks error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Teachters.route('/teacher/resources', methods=['GET', 'POST'])
@login_required
def resources():
    _session = Session()
    try:
        if 'username' not in session or session.get('role') != 'teacher':
            return redirect(url_for('Login.login'))

        teacher_id = session.get('userID')

        if request.method == 'POST':
            file_property = request.files.get('file')
            description = request.form.get('description', '')
            resource_type = request.form.get('resource_type', var.RESOURCE_TYPE[0])
            section_id = request.form.get('section_id')

            if file_property and file_property.filename and allowed_file(file_property.filename):
                filename = file_property.filename
                if resource_type in (var.RESOURCE_TYPE[0], var.RESOURCE_TYPE[1]):
                    dest_dir = var.WORK_SHEET_PATH
                    link_path = var.WORK_SHEET_LINK_PATH
                else:
                    dest_dir = var.EXTRA_RESOURCE_PATH
                    link_path = var.EXTRA_RESOURCE_LINK_PATH

                os.makedirs(dest_dir, exist_ok=True)
                file_property.save(os.path.join(dest_dir, filename))

                new_res = Resource(
                    ID=var.ID(),
                    section_id=section_id,
                    description=description,
                    file_name=filename,
                    path=link_path,
                    post_t=teacher_id,
                    post_a="None",
                    resource_type=resource_type,
                    valid=1
                )
                _session.add(new_res)
                _session.commit()
                return redirect(url_for('teacher.resources'))

        # Fetch sections taught by this teacher (excluding Forbidden)
        assignments = _session.query(thought).filter(
            thought.teacher_id == teacher_id,
            thought.access_level != 'Forbidden'
        ).all()
        # Find matching Sections rows
        teacher_sections = []
        for a in assignments:
            sec_row = _session.query(Sections).filter_by(grade=int(a.grade), section=a.section).first()
            if sec_row and sec_row not in teacher_sections:
                teacher_sections.append(sec_row)

        # Get resources uploaded by this teacher
        my_resources = _session.query(Resource).filter_by(post_t=teacher_id).all()

        return render_template(
            'teacher_resources.html',
            resources=my_resources,
            sections=teacher_sections,
            resource_types=var.RESOURCE_TYPE,
            active_page='resources'
        )
    except Exception as e:
        _session.rollback()
        var.log(f"Teacher resources error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()
