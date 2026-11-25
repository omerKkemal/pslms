from datetime import date

from database.modle import Semester


def is_assessment_type(assessment_name, assessment_type):
    words = ''.join(
        character if character.isalnum() else ' '
        for character in (assessment_name or '').casefold()
    ).split()
    if assessment_type == 'midterm':
        return bool({'mid', 'midterm'} & set(words))
    if assessment_type == 'final':
        return bool({'final', 'finals'} & set(words))
    return False


def get_semesters_and_selected(_session, requested_id=None):
    semesters = _session.query(Semester).order_by(Semester.starts_on.desc()).all()
    selected = next(
        (semester for semester in semesters if semester.ID == requested_id),
        None
    )
    if selected:
        return semesters, selected

    today = date.today()
    selected = next(
        (
            semester for semester in semesters
            if semester.closed_at is None
            and semester.starts_on <= today <= semester.ends_on
        ),
        None
    )
    if not selected:
        selected = next(
            (semester for semester in semesters if semester.starts_on <= today),
            semesters[-1] if semesters else None
        )
    return semesters, selected
