# =========================================================================== #
# Author: Omer Kemal                                                          #
# Website: https://www.johndoe.com                                            #
# Social Media:                                                               #
#   - Facebook: https://www.facebook.com/johndoe                              #
#   - Telegram: https://t.me/johndoe                                          #
#   - Twitter: @JohnDoe                                                       #
#   - GitHub: https://github.com/johndoe                                      #
# =========================================================================== #

from datetime import date, datetime, timedelta

from flask import request, render_template, Blueprint, url_for, redirect, session, flash
from flask_login import login_required
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os

from utility._templates_filters import getlist
from utility.data_processor import read_from_json,allowed_file
from database.modle import (
    Student, Teacher, CreatAssessment, Assessment, Sections, thought, Parent,
    ParentStudent,
    Subjects, Resource, DashboardActivity, AssessmentDeadline, ParentGradeAlert,
    Semester, SemesterGradeReport, SemesterSubjectAverage, rank
)
from database.manage_db import var, engine
from utility.semester_helpers import get_semesters_and_selected, is_assessment_type


Admin = Blueprint(
    var.ADMIN, __name__,
    static_folder=var.STATIC_FOLDE,
    static_url_path=var.STATIC_FOLDE_PATH,
    template_folder=var.TEMPLATE_FOLDER
)
Session = sessionmaker(bind=engine)
_session = Session()

Admin.add_app_template_filter(getlist, 'getList')


def _record_dashboard_activity(action):
    _session.add(DashboardActivity(action=action, actor=session['username']))


def _parse_house_number(value):
    try:
        house_number = int(value)
    except (TypeError, ValueError):
        return None
    return house_number if house_number > 0 else None


def _get_or_create_parent(
    fname, lname, house_number, student_id=None, phone='', email=''
):
    parent = _session.query(Parent).filter(
        func.lower(func.trim(Parent.fname)) == fname.strip().lower(),
        func.lower(func.trim(Parent.lname)) == lname.strip().lower(),
        Parent.hous_number == house_number
    ).first()
    created = parent is None

    if created:
        parent_id = var.ID()
        parent = Parent(
            ID=parent_id,
            fname=fname.strip(),
            lname=lname.strip(),
            student_id=student_id,
            hous_number=house_number,
            phone=phone,
            email=email,
            password=parent_id + fname.strip()
        )
        _session.add(parent)
        _session.flush()
    elif student_id and not parent.student_id:
        parent.student_id = student_id

    linked = False
    if student_id:
        link_exists = _session.query(ParentStudent).filter_by(
            parent_id=parent.ID,
            student_id=student_id
        ).first()
        if not link_exists:
            _session.add(ParentStudent(parent.ID, student_id))
            linked = True

    return parent, created, linked


def _is_assessment_type(assessment_name, assessment_type):
    return is_assessment_type(assessment_name, assessment_type)


def _collect_attention_items():
    deadlines = {
        deadline.assessment_type: deadline.due_at
        for deadline in _session.query(AssessmentDeadline).all()
    }
    now = datetime.now()
    assignments = (
        _session.query(thought, Teacher, Subjects)
        .join(Teacher, Teacher.ID == thought.teacher_id)
        .join(Subjects, Subjects.ID == thought.subject_id)
        .filter(thought.access_level == 'Read&Write')
        .all()
    )
    attention_items = []

    for assignment, teacher, subject in assignments:
        students = (
            _session.query(Student)
            .filter(
                Student.grade == int(assignment.grade),
                Student.section == assignment.section
            )
            .order_by(Student.fname, Student.lname)
            .all()
        )
        if not students:
            continue

        records = _session.query(Assessment).filter_by(
            teacher_id=teacher.ID,
            subject_id=subject.ID,
            grade=str(assignment.grade),
            section=assignment.section
        ).all()
        records_by_student = {}
        for record in records:
            records_by_student.setdefault(record.student_id, []).append(record)

        missing_grade = [
            student for student in students
            if not records_by_student.get(student.ID)
        ]
        if missing_grade:
            attention_items.append({
                'kind': 'missing_grade',
                'title': 'Missing grade (NG)',
                'teacher': teacher,
                'grade': assignment.grade,
                'section': assignment.section,
                'subject': subject.subject,
                'students': missing_grade,
                'due_at': None
            })

        for assessment_type, title in (
            ('midterm', 'Midterm grades overdue'),
            ('final', 'Final grades overdue')
        ):
            due_at = deadlines.get(assessment_type)
            if due_at is None or due_at > now:
                continue

            missing_exam_grade = [
                student for student in students
                if not any(
                    _is_assessment_type(record.AssessmentName, assessment_type)
                    for record in records_by_student.get(student.ID, [])
                )
            ]
            if missing_exam_grade:
                attention_items.append({
                    'kind': assessment_type,
                    'title': title,
                    'teacher': teacher,
                    'grade': assignment.grade,
                    'section': assignment.section,
                    'subject': subject.subject,
                    'students': missing_exam_grade,
                    'due_at': due_at
                })

    return attention_items


def _collect_system_notices(today=None, now=None):
    today = today or date.today()
    now = now or datetime.now()
    notices = []

    active_semester = _session.query(Semester).filter(
        Semester.starts_on <= today,
        Semester.ends_on >= today,
        Semester.closed_at.is_(None)
    ).order_by(Semester.starts_on.desc()).first()

    if active_semester:
        notices.append({
            'title': 'Active semester',
            'message': (
                f'{active_semester.name} is active through '
                f'{active_semester.ends_on:%B %d, %Y}.'
            ),
            'severity': 'info'
        })
    else:
        upcoming_semester = _session.query(Semester).filter(
            Semester.starts_on > today,
            Semester.closed_at.is_(None)
        ).order_by(Semester.starts_on).first()
        if upcoming_semester:
            notices.append({
                'title': 'Upcoming semester',
                'message': (
                    f'{upcoming_semester.name} starts '
                    f'{upcoming_semester.starts_on:%B %d, %Y}. '
                    'Assessments entered before then will not be assigned to a semester.'
                ),
                'severity': (
                    'warning'
                    if upcoming_semester.starts_on <= today + timedelta(days=7)
                    else 'info'
                )
            })
        else:
            notices.append({
                'title': 'No active semester',
                'message': (
                    'There is no active or upcoming semester. '
                    'New assessments will not be assigned to a semester.'
                ),
                'severity': 'warning'
            })

    attention_items = _collect_attention_items()
    missing_grade_groups = [
        item for item in attention_items if item['kind'] == 'missing_grade'
    ]
    if missing_grade_groups:
        group_count = len(missing_grade_groups)
        notices.append({
            'title': 'Grades need attention',
            'message': (
                f'{group_count} assigned class and subject group'
                f'{"s" if group_count != 1 else ""} have students without '
                'any recorded grades.'
            ),
            'severity': 'warning'
        })

    overdue_groups = {
        assessment_type: [
            item for item in attention_items if item['kind'] == assessment_type
        ]
        for assessment_type in ('midterm', 'final')
    }
    for deadline in _session.query(AssessmentDeadline).order_by(
        AssessmentDeadline.due_at
    ):
        if now < deadline.due_at <= now + timedelta(days=7):
            notices.append({
                'title': f'{deadline.assessment_type.title()} deadline approaching',
                'message': (
                    f'The configured deadline is '
                    f'{deadline.due_at:%B %d, %Y at %H:%M}.'
                ),
                'severity': 'warning'
            })
        elif deadline.due_at <= now and overdue_groups.get(deadline.assessment_type):
            groups = overdue_groups[deadline.assessment_type]
            group_count = len(groups)
            student_count = sum(len(item['students']) for item in groups)
            notices.append({
                'title': f'Missing {deadline.assessment_type} grades',
                'message': (
                    f'{group_count} class and subject group'
                    f'{"s" if group_count != 1 else ""} still have '
                    f'{student_count} student'
                    f'{"s" if student_count != 1 else ""} without '
                    f'{deadline.assessment_type} grades.'
                ),
                'severity': 'warning'
            })

    if active_semester:
        attention_event_count = _session.query(
            func.count(func.distinct(ParentGradeAlert.event_id))
        ).filter(
            ParentGradeAlert.semester_id == active_semester.ID,
            ParentGradeAlert.alert_type.in_(
                ('attention', 'assessment_attention')
            )
        ).scalar() or 0
        if attention_event_count:
            notices.append({
                'title': 'Parent grade alerts',
                'message': (
                    f'{attention_event_count} low-grade alert event'
                    f'{"s have" if attention_event_count != 1 else " has"} '
                    f'been recorded for {active_semester.name}.'
                ),
                'severity': 'warning'
            })

    return notices


def _publish_semester(_session, semester):
    attention_counts = {
        (student_id, subject_id): count
        for student_id, subject_id, count in _session.query(
            ParentGradeAlert.student_id,
            ParentGradeAlert.subject_id,
            func.count(func.distinct(ParentGradeAlert.event_id))
        )
        .filter(
            ParentGradeAlert.semester_id == semester.ID,
            ParentGradeAlert.alert_type.in_(
                ('attention', 'assessment_attention')
            )
        )
        .group_by(ParentGradeAlert.student_id, ParentGradeAlert.subject_id)
        .all()
    }

    averages = _session.query(SemesterSubjectAverage).filter_by(
        semester_id=semester.ID
    ).all()
    for average in averages:
        previous_report = (
            _session.query(SemesterGradeReport)
            .join(Semester, Semester.ID == SemesterGradeReport.semester_id)
            .filter(
                SemesterGradeReport.student_id == average.student_id,
                SemesterGradeReport.subject_id == average.subject_id,
                Semester.closed_at.isnot(None)
            )
            .order_by(Semester.closed_at.desc())
            .first()
        )
        _session.add(SemesterGradeReport(
            ID=var.ID(),
            semester_id=semester.ID,
            student_id=average.student_id,
            subject_id=average.subject_id,
            average=average.average,
            previous_average=previous_report.average if previous_report else None,
            attention_count=attention_counts.get(
                (average.student_id, average.subject_id), 0
            )
        ))

    semester.closed_at = datetime.now()


def _calculate_semester_ranks(_session, grade, section, semester_id):
    scored_students = (
        _session.query(
            SemesterSubjectAverage.student_id,
            func.avg(SemesterSubjectAverage.average)
        )
        .join(Student, Student.ID == SemesterSubjectAverage.student_id)
        .filter(
            Student.grade == grade,
            Student.section == section,
            SemesterSubjectAverage.semester_id == semester_id
        )
        .group_by(SemesterSubjectAverage.student_id)
        .all()
    )
    student_ids = [student_id for student_id, _ in scored_students]
    students = {
        student.ID: student
        for student in _session.query(Student).filter(Student.ID.in_(student_ids)).all()
    } if student_ids else {}
    ordered_scores = sorted(
        (
            (student_id, float(average))
            for student_id, average in scored_students
        ),
        key=lambda item: (
            -item[1],
            students[item[0]].fname,
            students[item[0]].lname,
            item[0]
        )
    )

    previous_average = None
    current_rank = 0
    for position, (student_id, average) in enumerate(ordered_scores, start=1):
        if average != previous_average:
            current_rank = position
        student_rank = _session.query(rank).filter_by(
            student_id=student_id,
            semester_id=semester_id
        ).first()
        if student_rank:
            student_rank.rank = current_rank
        else:
            _session.add(rank(
                ID=var.ID(),
                student_id=student_id,
                rank=current_rank,
                simister=1.0,
                semester_id=semester_id
            ))
        previous_average = average

    return len(ordered_scores)


def publish_expired_semesters():
    _session = Session()
    try:
        expired_semesters = _session.query(Semester).filter(
            Semester.ends_on < date.today(),
            Semester.closed_at.is_(None)
        ).all()
        for semester in expired_semesters:
            _publish_semester(_session, semester)
        if expired_semesters:
            _session.commit()
    except Exception as e:
        _session.rollback()
        var.log(f"Automatic semester report publishing error: {e}")
        raise
    finally:
        _session.close()


@Admin.route('/admin/panal/get_parents')
@login_required
def get_parents():
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                parents = _session.query(Parent).all()
                all_students = _session.query(Student).all()
                student_map = {s.ID: f"{s.fname} {s.lname}" for s in all_students}
                linked_students = {}
                if parents:
                    for parent_student in _session.query(ParentStudent).filter(
                        ParentStudent.parent_id.in_([p.ID for p in parents])
                    ).all():
                        linked_students.setdefault(
                            parent_student.parent_id, []
                        ).append(student_map.get(parent_student.student_id, ''))
                parent_list = []
                for p in parents:
                    parent_list.append({
                        'ID': p.ID,
                        'fname': p.fname,
                        'lname': p.lname,
                        'email': p.email,
                        'phone': p.phone,
                        'hous_number': p.hous_number,
                        'student_names': ', '.join(filter(
                            None, linked_students.get(p.ID, [])
                        ))
                    })
                return render_template('get_parents.html', parents=parent_list, all_students=all_students, active_page='get_parents')
            else:
                return redirect(url_for('event.unauthorized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error in get_parents: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route('/admin/panal/add_parent', methods=['POST'])
@login_required
def add_parent():
    try:
        if 'username' in session and session['role'] == 'admin':
            fname = request.form.get('fname', '').strip()
            lname = request.form.get('lname', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            student_id = request.form.get('student_id', '').strip() or None

            house_number = _parse_house_number(request.form.get('hous_number'))
            if not fname or not lname:
                flash('Enter the parent first and last name.', 'error')
                return redirect(url_for('admin.get_parents'))
            if house_number is None:
                flash('A positive house number is required.', 'error')
                return redirect(url_for('admin.get_parents'))
            if student_id and not _session.query(Student).filter_by(
                ID=student_id
            ).first():
                flash('Choose a valid student.', 'error')
                return redirect(url_for('admin.get_parents'))

            parent, created, linked = _get_or_create_parent(
                fname,
                lname,
                house_number,
                student_id=student_id,
                phone=phone,
                email=email
            )
            if created:
                _record_dashboard_activity('Added a parent')
            elif linked:
                _record_dashboard_activity('Linked existing parent to a student')
            _session.commit()
            flash(
                'Parent added successfully.' if created else
                ('Existing parent linked to the student.' if linked else
                 'That parent already exists for this house number.'),
                'success' if created or linked else 'info'
            )
            return redirect(url_for('admin.get_parents'))
        else:
            return redirect(url_for('event.unauthorized'))
    except Exception as e:
        _session.rollback()
        var.log(f"Error in add_parent: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route('/admin/panal/update_parent/<parent_id>', methods=['POST'])
@login_required
def update_parent(parent_id):
    try:
        if 'username' not in session or session.get('role') != 'admin':
            return redirect(url_for('event.unauthorized'))

        parent = _session.query(Parent).filter_by(ID=parent_id).first()
        if not parent:
            flash('Parent not found.', 'error')
            return redirect(url_for('admin.get_parents'))

        fname = request.form.get('fname', '').strip()
        lname = request.form.get('lname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        house_number = _parse_house_number(request.form.get('hous_number'))
        if not fname or not lname:
            flash('Enter the parent first and last name.', 'error')
            return redirect(url_for('admin.get_parents'))
        if house_number is None:
            flash('A positive house number is required.', 'error')
            return redirect(url_for('admin.get_parents'))

        duplicate = _session.query(Parent).filter(
            Parent.ID != parent.ID,
            func.lower(func.trim(Parent.fname)) == fname.lower(),
            func.lower(func.trim(Parent.lname)) == lname.lower(),
            Parent.hous_number == house_number
        ).first()
        if duplicate:
            flash(
                'Another parent already has this name and house number.',
                'error'
            )
            return redirect(url_for('admin.get_parents'))

        parent.fname = fname
        parent.lname = lname
        parent.email = email
        parent.phone = phone
        parent.hous_number = house_number
        _record_dashboard_activity('Updated a parent')
        _session.commit()
        flash('Parent information updated.', 'success')
        return redirect(url_for('admin.get_parents'))
    except Exception as e:
        _session.rollback()
        var.log(f"Error in update_parent: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route('/admin/panal/delete_parent', methods=['POST'])
@login_required
def delete_parent():
    try:
        if 'username' in session and session['role'] == 'admin':
            parent_id = request.form.get('id')
            if not parent_id and request.is_json:
                data = request.get_json()
                parent_id = data.get('id') if data else None

            if not parent_id:
                return redirect(url_for('admin.get_parents'))

            p = _session.query(Parent).filter_by(ID=parent_id).first()
            if p:
                _session.query(ParentStudent).filter_by(
                    parent_id=p.ID
                ).delete(synchronize_session=False)
                _session.delete(p)
                _record_dashboard_activity('Deleted a parent')
                _session.commit()

            if request.is_json:
                return {'message': 'Parent deleted successfully'}, 200
            return redirect(url_for('admin.get_parents'))
        else:
            return redirect(url_for('event.unauthorized'))
    except Exception as e:
        _session.rollback()
        var.log(f"Error in delete_parent: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route("/admin/Dashboard")
@login_required
def dashboard():
    if "username" in session:
        if session["role"] != "admin":
            return redirect(url_for('event.unauthorized'))
        
        total_students = _session.query(Student).count()
        total_teachers = _session.query(Teacher).count()
        total_sections = _session.query(Sections).count()
        total_resources = _session.query(Resource).count()

        # Gender values are stored as either M/F or Male/Female.
        male_count = _session.query(Student).filter(
            func.upper(Student.gender).in_(('M', 'MALE'))
        ).count()
        female_count = _session.query(Student).filter(
            func.upper(Student.gender).in_(('F', 'FEMALE'))
        ).count()
        recent_activities = (
            _session.query(DashboardActivity)
            .order_by(DashboardActivity.created_at.desc(), DashboardActivity.ID.desc())
            .limit(10)
            .all()
        )

        return render_template(
            'dashboard.html',
            total_students=total_students,
            total_teachers=total_teachers,
            total_sections=total_sections,
            total_resources=total_resources,
            male_count=male_count,
            female_count=female_count,
            recent_activities=recent_activities,
            system_notices=_collect_system_notices(),
            active_page='dashboard'
        )
    else:
        return redirect(url_for('Login.login'))


@Admin.route('/admin/reports', methods=['GET', 'POST'])
@login_required
def semester_reports():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('event.unauthorized'))

    try:
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            try:
                starts_on = date.fromisoformat(request.form.get('starts_on', ''))
                ends_on = date.fromisoformat(request.form.get('ends_on', ''))
            except (TypeError, ValueError):
                flash('Enter valid semester start and end dates.', 'error')
                return redirect(url_for('admin.semester_reports'))

            if not name or len(name) > 80:
                flash('Enter a semester name of 1 to 80 characters.', 'error')
                return redirect(url_for('admin.semester_reports'))
            if ends_on < starts_on:
                flash('The semester end date must be on or after its start date.', 'error')
                return redirect(url_for('admin.semester_reports'))
            overlapping_semester = _session.query(Semester).filter(
                Semester.starts_on <= ends_on,
                Semester.ends_on >= starts_on
            ).first()
            if overlapping_semester:
                flash('Semester dates cannot overlap another semester.', 'error')
                return redirect(url_for('admin.semester_reports'))
            if _session.query(Semester).filter_by(name=name).first():
                flash('A semester with that name already exists.', 'error')
                return redirect(url_for('admin.semester_reports'))

            _session.add(Semester(
                ID=var.ID(),
                name=name,
                starts_on=starts_on,
                ends_on=ends_on
            ))
            _session.commit()
            flash('Semester created. Grades entered within its dates will be reported when it ends.', 'success')
            return redirect(url_for('admin.semester_reports'))

        semesters = _session.query(Semester).order_by(
            Semester.starts_on.desc()
        ).all()
        _, selected_semester = get_semesters_and_selected(
            _session, request.args.get('semester_id')
        )
        grade_options = [
            grade for (grade,) in _session.query(Student.grade)
            .filter(Student.grade.isnot(None))
            .distinct()
            .order_by(Student.grade)
            .all()
        ]
        try:
            selected_grade = int(request.args.get('grade', ''))
        except (TypeError, ValueError):
            selected_grade = None
        if selected_grade not in grade_options:
            selected_grade = None

        section_query = _session.query(Student.section).filter(
            Student.section.isnot(None)
        )
        if selected_grade is not None:
            section_query = section_query.filter(Student.grade == selected_grade)
        sections = sorted({section for (section,) in section_query.distinct().all()})
        selected_section = request.args.get('section', '')
        if selected_section not in sections:
            selected_section = ''

        assessment_type = request.args.get('assessment_type', 'all').lower()
        if assessment_type not in ('all', 'midterm', 'final'):
            assessment_type = 'all'

        student_query = _session.query(Student)
        if selected_grade is not None:
            student_query = student_query.filter(Student.grade == selected_grade)
        if selected_section:
            student_query = student_query.filter(Student.section == selected_section)
        students = student_query.order_by(
            Student.grade, Student.section, Student.fname, Student.lname
        ).all()

        student_rows = []
        if selected_semester:
            semester_assessments = (
                _session.query(Assessment, Student)
                .join(Student, Student.ID == Assessment.student_id)
                .filter(Assessment.semester_id == selected_semester.ID)
            )
            if selected_grade is not None:
                semester_assessments = semester_assessments.filter(
                    Student.grade == selected_grade
                )
            if selected_section:
                semester_assessments = semester_assessments.filter(
                    Student.section == selected_section
                )

            assessment_counts = {}
            for assessment, student in semester_assessments.all():
                if assessment_type != 'all' and not is_assessment_type(
                    assessment.AssessmentName, assessment_type
                ):
                    continue
                assessment_counts[student.ID] = (
                    assessment_counts.get(student.ID, 0) + 1
                )

            averages_by_student = {}
            average_query = (
                _session.query(SemesterSubjectAverage, Subjects)
                .join(Subjects, Subjects.ID == SemesterSubjectAverage.subject_id)
                .filter(
                    SemesterSubjectAverage.semester_id == selected_semester.ID
                )
            )
            if students:
                average_query = average_query.filter(
                    SemesterSubjectAverage.student_id.in_(
                        [student.ID for student in students]
                    )
                )
            else:
                average_query = None
            if average_query is not None:
                for average, subject in average_query.all():
                    averages_by_student.setdefault(average.student_id, []).append(
                        average.average
                    )

            rank_by_student = {
                student_rank.student_id: student_rank.rank
                for student_rank in _session.query(rank).filter_by(
                    semester_id=selected_semester.ID
                ).all()
            }
            notice_counts = {
                student_id: event_count
                for student_id, event_count in _session.query(
                    ParentGradeAlert.student_id,
                    func.count(func.distinct(ParentGradeAlert.event_id))
                )
                .filter(
                    ParentGradeAlert.semester_id == selected_semester.ID
                )
                .group_by(ParentGradeAlert.student_id)
                .all()
            }

            for student in students:
                assessment_count = assessment_counts.get(student.ID, 0)
                if assessment_type != 'all' and assessment_count == 0:
                    continue
                subject_averages = averages_by_student.get(student.ID, [])
                student_rows.append({
                    'student': student,
                    'overall_average': (
                        sum(subject_averages) / len(subject_averages)
                        if subject_averages else None
                    ),
                    'assessment_count': assessment_count,
                    'rank': rank_by_student.get(student.ID),
                    'parent_notice_events': notice_counts.get(student.ID, 0)
                })

        return render_template(
            'semester_reports.html',
            semesters=semesters,
            selected_semester=selected_semester,
            grade_options=grade_options,
            selected_grade=selected_grade,
            sections=sections,
            selected_section=selected_section,
            assessment_type=assessment_type,
            student_rows=student_rows,
            today=date.today(),
            active_page='semester_reports'
        )
    except Exception as e:
        _session.rollback()
        var.log(f"Semester reports error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route('/admin/reports/calculate-ranks', methods=['POST'])
@login_required
def calculate_semester_ranks():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('event.unauthorized'))

    semester_id = request.form.get('semester_id', '')
    section = request.form.get('section', '').strip()
    assessment_type = request.form.get('assessment_type', 'all')
    if assessment_type not in ('all', 'midterm', 'final'):
        assessment_type = 'all'
    try:
        grade = int(request.form.get('grade', ''))
    except (TypeError, ValueError):
        flash('Choose a valid grade before calculating ranks.', 'error')
        return redirect(url_for('admin.semester_reports'))

    semester = _session.query(Semester).filter_by(ID=semester_id).first()
    if not semester or not section:
        flash('Choose a semester and section before calculating ranks.', 'error')
        return redirect(url_for(
            'admin.semester_reports',
            semester_id=semester_id,
            grade=grade
        ))

    try:
        ranked_count = _calculate_semester_ranks(
            _session, grade, section, semester.ID
        )
        if not ranked_count:
            flash('No semester averages are available for this class.', 'error')
        else:
            _session.commit()
            flash(f'Ranks calculated for {ranked_count} students.', 'success')
        return redirect(url_for(
            'admin.semester_reports',
            semester_id=semester.ID,
            grade=grade,
            section=section,
            assessment_type=assessment_type
        ))
    except Exception as e:
        _session.rollback()
        var.log(f"Semester rank calculation error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route('/admin/reports/student/<student_id>')
@login_required
def student_report_card(student_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('event.unauthorized'))

    try:
        student = _session.query(Student).filter_by(ID=student_id).first()
        if not student:
            flash('Student not found.', 'error')
            return redirect(url_for('admin.semester_reports'))

        semesters, selected_semester = get_semesters_and_selected(
            _session, request.args.get('semester_id')
        )
        if not selected_semester:
            flash('Create a semester before viewing a report card.', 'error')
            return redirect(url_for('admin.semester_reports'))

        assessments = (
            _session.query(Assessment, Subjects)
            .join(Subjects, Subjects.ID == Assessment.subject_id)
            .filter(
                Assessment.student_id == student.ID,
                Assessment.semester_id == selected_semester.ID
            )
            .order_by(Subjects.subject, Assessment.AssessmentName)
            .all()
        )
        score_rows = []
        for assessment, subject in assessments:
            definition = _session.query(CreatAssessment).filter_by(
                Assessment_of=assessment.teacher_id,
                Assessment_name=assessment.AssessmentName
            ).first()
            max_score = (
                float(definition.Mark)
                if definition and definition.Mark and definition.Mark > 0
                else 100.0
            )
            score_rows.append({
                'assessment': assessment,
                'subject_name': subject.subject,
                'max_score': max_score,
                'percentage': float(assessment.ScoreMark) / max_score * 100,
                'assessment_type': (
                    'Midterm'
                    if is_assessment_type(assessment.AssessmentName, 'midterm')
                    else (
                        'Final'
                        if is_assessment_type(assessment.AssessmentName, 'final')
                        else 'Other'
                    )
                )
            })

        published_averages = {
            report.subject_id: report
            for report in _session.query(SemesterGradeReport).filter_by(
                student_id=student.ID,
                semester_id=selected_semester.ID
            ).all()
        }
        subject_averages = (
            _session.query(SemesterSubjectAverage, Subjects)
            .join(Subjects, Subjects.ID == SemesterSubjectAverage.subject_id)
            .filter(
                SemesterSubjectAverage.student_id == student.ID,
                SemesterSubjectAverage.semester_id == selected_semester.ID
            )
            .order_by(Subjects.subject)
            .all()
        )
        average_rows = []
        for average, subject in subject_averages:
            report = published_averages.get(average.subject_id)
            average_rows.append({
                'subject_name': subject.subject,
                'average': report.average if report else average.average,
                'previous_average': report.previous_average if report else None,
                'attention_count': report.attention_count if report else None
            })

        parent_query = (
            _session.query(Parent)
            .join(ParentStudent, ParentStudent.parent_id == Parent.ID)
            .filter(ParentStudent.student_id == student.ID)
        )
        direct_parents = parent_query.all()
        household_numbers = {
            parent.hous_number for parent in direct_parents
            if parent.hous_number and parent.hous_number > 0
        }
        if household_numbers:
            parents = _session.query(Parent).filter(
                Parent.hous_number.in_(household_numbers)
            ).all()
        else:
            parents = direct_parents

        parent_alert_rows = (
            _session.query(ParentGradeAlert, Subjects, Parent)
            .join(Subjects, Subjects.ID == ParentGradeAlert.subject_id)
            .join(Parent, Parent.ID == ParentGradeAlert.parent_id)
            .filter(
                ParentGradeAlert.student_id == student.ID,
                ParentGradeAlert.semester_id == selected_semester.ID
            )
            .order_by(
                ParentGradeAlert.parent_id,
                ParentGradeAlert.created_at,
                ParentGradeAlert.ID
            )
            .all()
        )
        parents_by_id = {parent.ID: parent for parent in parents}
        alerts_by_parent = {}
        for alert, subject, parent in parent_alert_rows:
            parents_by_id[parent.ID] = parent
            alerts_by_parent.setdefault(alert.parent_id, []).append({
                'alert': alert,
                'subject_name': subject.subject
            })

        parent_notice_history = []
        for parent in sorted(
            parents_by_id.values(), key=lambda item: (item.fname, item.lname, item.ID)
        ):
            history = alerts_by_parent.get(parent.ID, [])
            history_rows = []
            for index, row in enumerate(history):
                alert = row['alert']
                improved_event = None
                if alert.alert_type == 'attention':
                    improved_event = next(
                        (
                            later['alert'] for later in history[index + 1:]
                            if later['alert'].subject_id == alert.subject_id
                            and later['alert'].assessment_name is None
                            and later['alert'].average > alert.average
                        ),
                        None
                    )
                elif alert.alert_type == 'assessment_attention':
                    improved_event = next(
                        (
                            later['alert'] for later in history[index + 1:]
                            if later['alert'].subject_id == alert.subject_id
                            and later['alert'].assessment_name == alert.assessment_name
                            and later['alert'].alert_type in (
                                'assessment_attention', 'assessment_recovery'
                            )
                            and later['alert'].average > alert.average
                        ),
                        None
                    )
                history_rows.append({
                    **row,
                    'improved_event': improved_event
                })
            parent_notice_history.append({
                'parent': parent,
                'notice_count': len(history),
                'history': history_rows
            })

        student_rank = _session.query(rank).filter_by(
            student_id=student.ID,
            semester_id=selected_semester.ID
        ).first()
        overall_average = (
            sum(row['average'] for row in average_rows) / len(average_rows)
            if average_rows else None
        )

        return render_template(
            'student_report_card.html',
            student=student,
            semesters=semesters,
            selected_semester=selected_semester,
            score_rows=score_rows,
            average_rows=average_rows,
            overall_average=overall_average,
            student_rank=student_rank.rank if student_rank else None,
            parent_notice_history=parent_notice_history,
            active_page='semester_reports'
        )
    except Exception as e:
        _session.rollback()
        var.log(f"Student report card error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


#Similarly for other routes: 'admin_panal', 'add_students', 'add_teacher', 'resource_option', 'section_info', 'get_teachers'.

# student info (done!!!!)
@Admin.route('/admin/panal', methods=['GET'])
@login_required
def admin():
    if "username" in session:
        if session["role"] == "admin":
            # Load grades and sections from memory.json
            data, _data = read_from_json()
            grades = data.Permanent.grade
            sections = data.Permanent.section

            # Gender mapping
            gender = {'male': 'M', 'female': 'F'}

            resource_types = var.RESOURCE_TYPE

            assessment_deadlines = {
                deadline.assessment_type: deadline.due_at.strftime('%Y-%m-%dT%H:%M')
                for deadline in _session.query(AssessmentDeadline).all()
            }

            return render_template(
                'admin_panal.html',
                active_page='admin_panal',
                grades=grades,
                sections=sections,
                gender=gender,
                resource_types=resource_types,
                assessment_deadlines=assessment_deadlines,
                attention_items=_collect_attention_items()
            )
        else:
            return redirect(url_for('event.unauthorized'))
    else:
        return redirect(url_for('Login.login'))


@Admin.route('/admin/panal/assessment-deadlines', methods=['POST'])
@login_required
def save_assessment_deadlines():
    try:
        if 'username' not in session or session.get('role') != 'admin':
            return redirect(url_for('event.unauthorized'))

        for assessment_type in ('midterm', 'final'):
            value = request.form.get(f'{assessment_type}_due_at', '').strip()
            deadline = _session.query(AssessmentDeadline).filter_by(
                assessment_type=assessment_type
            ).first()

            if value:
                try:
                    due_at = datetime.fromisoformat(value)
                except ValueError:
                    flash(f'Enter a valid {assessment_type} deadline.', 'error')
                    return redirect(url_for('admin.admin'))

                if deadline:
                    deadline.due_at = due_at
                else:
                    _session.add(AssessmentDeadline(
                        assessment_type=assessment_type,
                        due_at=due_at
                    ))
            elif deadline:
                _session.delete(deadline)

        _session.commit()
        flash('Assessment deadlines saved.', 'success')
        return redirect(url_for('admin.admin'))
    except Exception as e:
        _session.rollback()
        var.log(f"Error saving assessment deadlines: {e}")
        flash('Could not save assessment deadlines.', 'error')
        return redirect(url_for('admin.admin'))
    finally:
        _session.close()


# add student(done!!!)
@Admin.route('/admin/panal/add_students', methods=['GET', 'POST'])
@login_required
def add_students():
    try:
        if 'username' in session:
            data, _data = read_from_json()
            gender = data.Permanent.Gender
            grades = data.Permanent.grade
            sections = data.Permanent.section
            if session['role'] == 'admin':
                if request.method == 'POST':
                    fname = request.form['fname']
                    mname = request.form['mname']
                    lname = request.form['lname']
                    Grade = request.form['grade']
                    _gender = request.form["gender"]
                    _Section = request.form['section']
                    parent_hous_number = _parse_house_number(
                        request.form.get('parent_hous_number')
                    )
                    if parent_hous_number is None:
                        flash('A positive parent house number is required.', 'error')
                        return redirect(url_for('admin.admin'))
                    ID = var.ID()
                    exist = _session.query(Sections).filter(
                        Sections.section == _Section.upper(),
                        Sections.grade == Grade
                    ).first()

                    reg = Student(
                        ID, fname, mname, lname, _gender,
                        ID+fname, _Section.upper(), Grade
                    )
                    print(reg)
                    try:
                        if not exist:
                            section = Sections(var.ID(), _Section.upper(), Grade)
                            _session.add(section)
                            _session.commit()
                            print('section was added')

                        _session.add(reg)

                        parent_phone = request.form.get('parent_phone', '').strip()
                        parent_email = request.form.get('parent_email', '').strip()
                        parent, parent_created, _ = _get_or_create_parent(
                            mname,
                            lname,
                            parent_hous_number,
                            student_id=ID,
                            phone=parent_phone,
                            email=parent_email
                        )

                        _record_dashboard_activity('Added a student')
                        _session.commit()
                        print(
                            'student and parent were added' if parent_created else
                            'student added and existing parent linked'
                        )
                        return redirect(url_for('event.successful'))
                    except Exception as e:
                        _session.rollback()
                        var.log(f"Error occurred: {e}")
                        return redirect(url_for('event.internal_server_error'))
                else:
                    return 'unvalid request method'
            else:
                return redirect(url_for('event.unautrized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


# add student()
@Admin.route('/admin/panal/add_student/<grade>/<section>', methods=['GET', 'POST'])
@login_required
def add_student(grade=None, section=None):
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                data, _data = read_from_json()
                gender = data.Permanent.Gender
                if request.method == 'POST':
                    if grade and section:
                        fname = request.form['fname']
                        mname = request.form['mname']
                        lname = request.form['lname']
                        _gender = request.form["gender"]
                        parent_hous_number = _parse_house_number(
                            request.form.get('parent_hous_number')
                        )
                        if parent_hous_number is None:
                            flash(
                                'A positive parent house number is required.',
                                'error'
                            )
                            return redirect(url_for(
                                'admin.add_student',
                                grade=grade,
                                section=section
                            ))
                        ID = var.ID()
                        data, _data = read_from_json()
                        gender = data.Permanent.Gender
                        reg = Student(
                            ID, fname, mname,
                            lname, _gender, ID+fname, section.upper(), grade
                        )
                        print(reg)
                        try:
                            _session.add(reg)

                            parent_phone = request.form.get('parent_phone', '').strip()
                            parent_email = request.form.get('parent_email', '').strip()
                            parent, parent_created, _ = _get_or_create_parent(
                                mname,
                                lname,
                                parent_hous_number,
                                student_id=ID,
                                phone=parent_phone,
                                email=parent_email
                            )

                            _record_dashboard_activity('Added a student')
                            _session.commit()
                            print(
                                'student and parent were added' if parent_created else
                                'student added and existing parent linked'
                            )
                            _session.close()
                            return redirect(url_for('event.successful'))
                        except Exception as e:
                            _session.rollback()
                            var.log(f"Error occurred: {e}")
                            return redirect(url_for('event.internal_server_error'))
                    else:
                        return redirect(url_for('event.error'))
                else:
                    data, _data = read_from_json()
                    gender = data.Permanent.Gender
                    return render_template('add_student.html', gender=gender, grade=grade, section=section)
            else:
                return redirect(url_for('event.unautrized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route('/admin/panal/section_info')
@login_required
def info():
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                sections = _session.query(Sections).all()
                print(sections)
                return render_template('info_section.html', sections=sections,active_page='section_info')
            else:
                return redirect(url_for('event.unautrized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route('/admin/panal/get_students/<grade>/<section>')
@login_required
def get_students(grade=False, section=None):
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                if grade and section:
                    students = _session.query(Student).filter_by(grade=grade, section=section).all()
                    return render_template(
                        'get_students.html', students=students, grade=grade, section=section
                        )
                else:
                    return 'No grade provided'
            else:
                return redirect(url_for('event.unauthorized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()

# update basic info(name and gender)
@Admin.route('/admin/panal/update_student_Basic/<ID>', methods=['GET', 'POST'])
@login_required
def update_student_Basic(ID):
    try:
        if 'username' in session:
            _student = _session.query(Student).filter_by(ID=ID).all()
            student = getlist(_student)
            data, _data = read_from_json()
            sections = data.Permanent.section
            grades = data.Permanent.grade
            gender = data.Permanent.Gender
            if session['role'] == 'admin':
                if request.method == 'GET':
                    return render_template('basic_update.html', student=student,gender=gender,grades=grades,sections=sections)
                elif request.method == 'POST':
                    student_fname = request.form['fname']
                    student_mname = request.form['mname']
                    student_lname = request.form['lname']
                    student_gender = request.form["gender"]

                    updated_students = _session.query(Student).filter_by(ID=ID).update({
                        'fname': student_fname,
                        'mname': student_mname,
                        'lname': student_lname,
                        'gender': student_gender
                    })
                    if updated_students:
                        _record_dashboard_activity('Updated a student')
                    _session.commit()
                    _session.close()
                    print(student)
                    return redirect(url_for('event.successful'))
            else:
                return redirect(url_for('event.unauthorized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


# reset password
@Admin.route('/admin/panal/reset_password/<role>/<ID>')
@login_required
def reset_password(role,ID):
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                if role == 'teacher':
                    endpoint = "info"
                    teacher = getlist(_session.query(Teacher).filter_by(ID=ID).all())
                    new_password = teacher[0][0] + teacher[0][1]
                    _session.query(Teacher).filter_by(ID=ID).update({
                        'password': new_password
                    })
                    _record_dashboard_activity('Reset a teacher password')
                elif role == "student":
                    endpoint = "options"
                    student = getlist(_session.query(Student).filter_by(ID=ID).all())
                    new_password = student[0][0] + student[0][1]
                    _session.query(Student).filter_by(ID=ID).update({
                        'password': new_password
                    })
                    _record_dashboard_activity('Reset a student password')
                elif role == 'parent':
                    parent = _session.query(Parent).filter_by(ID=ID).first()
                    if parent:
                        parent.password = parent.ID + parent.fname
                        _record_dashboard_activity('Reset a parent password')
                        _session.commit()
                    return redirect(url_for("admin.get_parents"))
                
                _session.commit()
                return redirect(url_for(f"admin.update_{endpoint}",ID=ID))
            else:
                return redirect(url_for('event.unauthorized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error at reset occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()
# update advance(section , grade and change password)
@Admin.route('/admin/panal/update_options/<ID>')
@login_required
def update_options(ID):
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                _student = _session.query(Student).filter_by(ID=ID).all()
                student = getlist(_student)
            
                return render_template('update_options.html', student=student)
            else:
                return redirect(url_for('event.unauthorized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


# teacher
@Admin.route('/admin/panal/add_teacher',methods=['POST', 'GET'])
@login_required
def add_teacher():
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                if request.method == 'POST':
                    fname = request.form["fname"]
                    mname = request.form["mname"]
                    lname = request.form["lname"]
                    gender = request.form["gender"]
                    try:
                        teacher_id = var.ID()
                        teacher = Teacher(
                            teacher_id, fname, mname,
                            lname, gender, teacher_id + fname
                        )
                        _session.add(teacher)
                        _record_dashboard_activity('Added a teacher')
                        _session.commit()
                        return redirect(url_for('event.successful'))
                    except Exception as e:
                        print(e)
                        _session.rollback()
                        return redirect(url_for('event.internal_server_error'))
                elif request.method == "GET":
                    return 'unvalid request method'
            else:
                return redirect(url_for('event.unauthorized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()

@Admin.route("/admin/panal/get_teachers")
@login_required
def get_teacher():
    try:
        if "username" in session:
            if session["role"] == "admin":
                teachers = _session.query(Teacher).all()
                gender = {'male': 'M', 'female': 'F'}
                return render_template("get_teacher.html", teachers=teachers,active_page='get_teachers',gender=gender)
            else:
                return redirect(url_for('event.unauthorized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route("/admin/panal/update/<ID>")
@login_required
def update_info(ID):
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                teacher = _session.query(Teacher).filter_by(ID=ID).all()
                teacher = getlist(teacher)
            
                return render_template('update_info.html', teacher=teacher)
            else:
                return redirect(url_for('event.unauthorized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()

@Admin.route('/admin/panal/add_subject_to_teacher/<ID>',methods=['POST','GET'])
@login_required
def add_subject_to_teacher(ID=None):
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                if request.method == 'POST':
                    if ID:
                        subjects = request.form.getlist('subjects')
                        # fallback if single select was passed
                        if not subjects and 'subject' in request.form:
                            subjects = [request.form['subject']]
                        grade = request.form['grade']
                        sections = request.form.getlist('sections')

                        for subject in subjects:
                            for section in sections:
                                # check if assignment already exists
                                existing = _session.query(thought).filter_by(
                                    subject_id=subject,
                                    teacher_id=ID,
                                    grade=str(grade),
                                    section=section
                                ).first()
                                if not existing:
                                    try:
                                        _thought = thought(
                                            var.ID(), subject, ID, str(grade), section, var.ACCSESS[1]
                                        )
                                        _session.add(_thought)
                                    except Exception as e:
                                        _session.rollback()
                                        var.log(f"Error in add_subject_to_teacher: {e}")
                        _session.commit()
                        return redirect(url_for('event.successful'))
                    else:
                        return redirect(url_for('event.error'))
                else:
                    data = read_from_json()[0]
                    teacher = _session.query(Teacher).filter_by(ID=ID).all()
                    subjects = getlist(_session.query(Subjects).all())
                    grades = data.Permanent.grade
                    sections = data.Permanent.section
                    return render_template(
                        'add_subject_to_teacher.html', teacher=getlist(teacher),
                        sections=sections, grades=grades, subjects=subjects
                    )
            else:
                return redirect(url_for('event.unauthorized'))
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route('/admin/panal/remove_subject_from_teacher/<ID>',methods=['POST','GET'])
@login_required
def remove_subject_from_teacher(ID):
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                if request.method == 'GET':
                    subject_and_gerad = getlist(_session.query(thought).filter_by(teacher_id=ID))
                    by_section = {}
                    sub_id = []
                    sub = ''
                    for i, subject in enumerate(subject_and_gerad):
                        sub_id.append(subject[1])
                         # If it's the first subject, initialize the dictionary with this sub_id
                        if i == 0:
                            print(sub_id)
                            sub = getlist(_session.query(Subjects).filter_by(ID=sub_id[0]).all())[0][1]
                            by_section[sub] = [[subject[0],subject[3], subject[4]]]
                        else:
                            print(sub_id)
                            # If the current sub_id matches the previous one, append to the existing list
                            if sub_id[0] == subject[1]:
                                by_section[sub].append([subject[0],subject[3], subject[4]])
                            else:
                                # If the sub_id changes, initialize a new entry for the new sub_id
                                sub_id[0] = subject[1]
                                sub = getlist(_session.query(Subjects).filter_by(ID=subject[1]).all())[0][1]
                                by_section[sub] = [[subject[0],subject[3], subject[4]]]
                    return render_template('remove_subject_from_teacher.html', by_section=by_section,access=var.ACCSESS,ID=ID)
                
                elif request.method == "POST":
                    thoughts = getlist(_session.query(thought).filter_by(teacher_id=ID).all())
                    accsess = var.ACCSESS
                    old_sub = []
                    for i,_thought in enumerate(thoughts):
                        sub = _thought[0]
                        print("id--",sub)
                        try:
                            if i == 0:
                                old_sub.append(sub)
                            else:
                                if sub != old_sub[0]:
                                    old_sub[0] = sub
                            
                            print(sub)
                            acc = request.form[f'{sub}']

                            print(acc)

                            _session.query(thought).filter_by(teacher_id=ID,ID=acc.split('-')[0]).update({
                                'access_level': acc.split('-')[1]
                            })
                        except Exception as e:
                            print(e)
                    _session.commit()
                    return redirect(url_for('event.successful'))
            
            else:
                return redirect(url_for('event.unauthorized'))
        else:
             return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(f"Error occurred: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()

@Admin.route('/admin/panal/edit_teacher_info/<ID>',methods=['POST','GET'])
@login_required
def edit_teacher_basic_info(ID=None):
    if 'username' in session:
        if session['role'] == 'admin':
            teacher = getlist(_session.query(Teacher).filter_by(ID=ID).all())
            data, _data = read_from_json()
            gender = data.Permanent.Gender
            if request.method == "GET":
                return render_template('edit_teacher_info.html', gender=gender,teacher=teacher)
            elif request.method == "POST":
                teacher_fname = request.form['fname']
                teacher_mname = request.form['mname']
                teacher_lname = request.form['lname']
                teacher_gender = request.form['gender']
                try:
                    updated_teachers = _session.query(Teacher).filter_by(ID=ID).update({
                        'fname': teacher_fname,
                        'mname': teacher_mname,
                        'lname': teacher_lname,
                        'gender': teacher_gender
                    })
                    if updated_teachers:
                        _record_dashboard_activity('Updated a teacher')
                    _session.commit()
                    return render_template('edit_teacher_info.html', gender=gender,teacher=teacher)
                except Exception as e:
                    _session.rollback()
                    print(e)
                    return 'error'

        else:
            return redirect(url_for('event.unauthorized'))
    else:
        return redirect(url_for('Login.login'))


@Admin.route("/add_resource", methods=['POST', 'GET'])
@Admin.route("/admin/panal/add_resource", methods=['POST', 'GET'])
@login_required
def add_resourc():
    try:
        if 'username' not in session or session.get('role') != 'admin':
            return redirect(url_for('event.unauthorized'))

        data, _data = read_from_json()
        grades = data.Permanent.grade
        sections = data.Permanent.section

        if request.method == 'GET':
            return render_template(
                'uplaod_resource.html',
                grades=grades,
                sections=sections,
                resource_types=var.RESOURCE_TYPE
            )

        file_property = request.files.get('files')
        description = request.form.get('description', '').strip()
        resource_type = request.form.get('resource_type', '')
        section_name = request.form.get('section', '').strip().upper()
        try:
            grade = int(request.form.get('grade', ''))
        except (TypeError, ValueError):
            flash('Choose a valid grade.', 'error')
            return redirect(url_for('admin.admin'))

        if grade not in grades or section_name not in sections:
            flash('Choose a grade and section from the available options.', 'error')
            return redirect(url_for('admin.admin'))
        if resource_type not in var.RESOURCE_TYPE:
            flash('Choose Assignment or Worksheet as the resource type.', 'error')
            return redirect(url_for('admin.admin'))
        filename = secure_filename(file_property.filename) if file_property and file_property.filename else ''
        if not filename or not allowed_file(filename):
            flash('Choose a supported resource file.', 'error')
            return redirect(url_for('admin.admin'))

        section_record = _session.query(Sections).filter_by(
            grade=grade,
            section=section_name
        ).first()
        if not section_record:
            section_record = Sections(var.ID(), section_name, grade)
            _session.add(section_record)
            _session.flush()

        os.makedirs(var.WORK_SHEET_PATH, exist_ok=True)
        file_property.save(os.path.join(var.WORK_SHEET_PATH, filename))
        _session.add(Resource(
            ID=var.ID(),
            section_id=section_record.ID,
            description=description,
            file_name=filename,
            path=var.WORK_SHEET_LINK_PATH,
            post_t='None',
            post_a=session['userID'],
            resource_type=resource_type,
            valid=1
        ))
        _record_dashboard_activity('Uploaded a resource')
        _session.commit()
        flash('Resource uploaded successfully.', 'success')
        return redirect(url_for('admin.admin'))
    except Exception as e:
        _session.rollback()
        var.log(f"Resource upload error: {e}")
        return redirect(url_for('event.internal_server_error'))
    finally:
        _session.close()


@Admin.route("/view_resource")
@login_required
def view_resour():
    try:
        if "username" in session:
            role = session['role']
            all_resources = getlist(_session.query(Resource).all())
            data, _data = read_from_json()
            return render_template(
                'view_resources.html',
                all_resources=all_resources,
                role=role,
                resource_types=var.RESOURCE_TYPE,
                grades=data.Permanent.grade,
                sections=data.Permanent.section
            )
        else:
            return redirect(url_for('Login.login'))
    except Exception as e:
        var.log(e)
        return 'error'

# Delete

@Admin.route('/admin/panal/delete_student', methods=['POST'])
@login_required
def delete_student():
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                data = request.get_json()
                student = _session.query(Student).filter_by(ID=data['id']).first()

                if student is None:
                    return {'message': 'Student not found'}, 404  # Return error if student doesn't exist

                _session.delete(student)
                _record_dashboard_activity('Deleted a student')
                _session.commit()

                return {'message': 'Student deleted successfully'}, 200  # Return success message as JSON

            else:
                return {'message': 'Unauthorized access'}, 403  # Return unauthorized status if user is not admin
        else:
            return {'message': 'Not logged in'}, 401  # Return not authorized status if session doesn't exist

    except Exception as e:
        _session.rollback()  # Rollback if any error occurs
        var.log(f"Error occurred: {e}")
        return {'message': 'An error occurred while deleting student'}, 500  # Return general error response

    finally:
        _session.close()  # Ensure session is closed


@Admin.route('/admin/panal/delete_resource', methods=['POST'])
@login_required
def delete_resource():
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                data = request.get_json()
                resource = getlist(_session.query(Resource).filter_by(ID=data['id']).all())
                
                print('omer',resource)

                if resource is None:
                    return {'message': 'Resource not found'}, 404  # Return error if Teacher doesn't exist
                
                if 'work_sheet' in resource[0][4]:
                     path = os.path.join(var.WORK_SHEET_PATH,resource[0][3])
                else:
                    path = os.path.join(var.EXTRA_RESOURCE_PATH ,resource[0][3])
                if os.path.exists(path):
                    os.remove(path)
                    print('path',path)
                delete = _session.query(Resource).filter_by(ID=data['id']).first()
                _session.delete(delete)
                _record_dashboard_activity('Deleted a resource')
                _session.commit()

                return {'message': 'Resource deleted successfully'}, 200  # Return success message as JSON

            else:
                return {'message': 'Unauthorized access'}, 403  # Return unauthorized status if user is not admin
        else:
            return {'message': 'Not logged in'}, 401  # Return not authorized status if session doesn't exist

    except Exception as e:
        _session.rollback()  # Rollback if any error occurs
        var.log(f"Error occurred: {e}")
        return {'message': 'An error occurred while deleting Resource'}, 500  # Return general error response

    finally:
        _session.close()  # Ensure session is closed


@Admin.route('/admin/panal/delete_teacher', methods=['POST'])
@login_required
def delete_teacher():
    try:
        if 'username' in session:
            if session['role'] == 'admin':
                data = request.get_json()
                student = _session.query(Teacher).filter_by(ID=data['id']).first()

                if student is None:
                    return {'message': 'Teacher not found'}, 404  # Return error if Teacher doesn't exist

                _session.delete(student)
                _record_dashboard_activity('Deleted a teacher')
                _session.commit()

                return {'message': 'Teacher deleted successfully'}, 200  # Return success message as JSON

            else:
                return {'message': 'Unauthorized access'}, 403  # Return unauthorized status if user is not admin
        else:
            return {'message': 'Not logged in'}, 401  # Return not authorized status if session doesn't exist

    except Exception as e:
        _session.rollback()  # Rollback if any error occurs
        var.log(f"Error occurred: {e}")
        return {'message': 'An error occurred while deleting Teacher'}, 500  # Return general error response

    finally:
        _session.close()  # Ensure session is closed

