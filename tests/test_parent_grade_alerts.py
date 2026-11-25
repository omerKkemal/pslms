import unittest
import importlib
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.modle import (
    Assessment, Base, CreatAssessment, Parent, ParentStudent, ParentGradeAlert, Semester,
    SemesterGradeReport, SemesterSubjectAverage, Student, Subjects, Teacher
)
from teacher.Teacher import (
    _calculate_subject_average, _notify_parents_of_assessment_result,
    _notify_parents_of_grade_change
)


class ParentGradeAlertTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

        self.session.add_all([
            Student('S1', 'Ava', 'M', 'Student', 'F', 'password', 'A', 1),
            Student('S2', 'Ben', 'M', 'Student', 'M', 'password', 'A', 1),
            Parent('P1', 'Parent', 'One', student_id='S1', hous_number=12),
            Parent('P2', 'Parent', 'Two', student_id='S2', hous_number=12),
            ParentStudent('P1', 'S1'),
            ParentStudent('P2', 'S2'),
            Subjects('SUB1', 'Math', 'ReadOnly'),
            Teacher('T1', 'Class', 'Teacher', 'One', 'M', 'password'),
            CreatAssessment('DEF1', 'Quiz', 'T1', 100),
            Semester(
                ID='SEM1', name='Term 1',
                starts_on=date(2026, 1, 1), ends_on=date(2026, 6, 30)
            ),
            Semester(
                ID='SEM2', name='Term 2',
                starts_on=date(2026, 7, 1), ends_on=date(2026, 12, 31)
            )
        ])
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_low_assessment_alert_is_saved_for_each_household_parent(self):
        _notify_parents_of_assessment_result(
            self.session, 'S1', 'SUB1', 'SEM1', 'Midterm Exam', None, 45
        )
        self.session.commit()

        alerts = self.session.query(ParentGradeAlert).all()
        self.assertEqual({alert.parent_id for alert in alerts}, {'P1', 'P2'})
        self.assertEqual(
            {alert.alert_type for alert in alerts}, {'assessment_attention'}
        )
        self.assertEqual({alert.average for alert in alerts}, {45})
        self.assertEqual({alert.assessment_name for alert in alerts}, {'Midterm Exam'})
        self.assertEqual({alert.semester_id for alert in alerts}, {'SEM1'})
        self.assertEqual(len({alert.event_id for alert in alerts}), 1)

    def test_assessment_recovery_is_recorded_after_a_low_result(self):
        _notify_parents_of_assessment_result(
            self.session, 'S1', 'SUB1', 'SEM1', 'Midterm Exam', 45, 55
        )
        self.session.commit()

        alerts = self.session.query(ParentGradeAlert).all()
        self.assertEqual(
            {alert.alert_type for alert in alerts}, {'assessment_recovery'}
        )
        self.assertEqual({alert.previous_average for alert in alerts}, {45})
        self.assertEqual({alert.average for alert in alerts}, {55})

    def test_assessment_at_exactly_fifty_percent_does_not_trigger_low_alert(self):
        created = _notify_parents_of_assessment_result(
            self.session, 'S1', 'SUB1', 'SEM1', 'Midterm Exam', None, 50
        )

        self.assertFalse(created)
        self.assertEqual(self.session.query(ParentGradeAlert).count(), 0)

    def test_improvement_is_logged_when_average_rises_above_threshold(self):
        _notify_parents_of_grade_change(
            self.session, 'S1', 'SUB1', 'SEM1', 45, 55
        )
        self.session.commit()

        alerts = self.session.query(ParentGradeAlert).all()
        self.assertEqual(len(alerts), 2)
        self.assertEqual({alert.alert_type for alert in alerts}, {'improvement'})
        self.assertEqual({alert.previous_average for alert in alerts}, {45})
        self.assertEqual({alert.average for alert in alerts}, {55})

    def test_unchanged_or_lower_passing_average_does_not_create_alert(self):
        _notify_parents_of_grade_change(
            self.session, 'S1', 'SUB1', 'SEM1', 55, 55
        )
        _notify_parents_of_grade_change(
            self.session, 'S1', 'SUB1', 'SEM1', 55, 54
        )
        self.session.commit()

        self.assertEqual(self.session.query(ParentGradeAlert).count(), 0)

    def test_subject_average_is_scoped_to_the_selected_semester(self):
        self.session.add_all([
            Assessment(
                'A1', 'S1', 'T1', 'SUB1', '1', 'A', 'Quiz', 40,
                semester_id='SEM1'
            ),
            Assessment(
                'A2', 'S1', 'T1', 'SUB1', '1', 'A', 'Quiz', 80,
                semester_id='SEM2'
            )
        ])
        self.session.commit()

        self.assertEqual(
            _calculate_subject_average(self.session, 'S1', 'SUB1', 'SEM1'),
            40
        )
        self.assertEqual(
            _calculate_subject_average(self.session, 'S1', 'SUB1', 'SEM2'),
            80
        )

    def test_expired_semester_is_published_from_its_own_averages(self):
        today = date.today()
        self.session.add_all([
            Semester(
                ID='PAST', name='Past Term',
                starts_on=today - timedelta(days=30),
                ends_on=today - timedelta(days=1)
            ),
            SemesterSubjectAverage(
                ID='PASTAVG', semester_id='PAST', student_id='S1',
                subject_id='SUB1', average=42
            ),
            ParentGradeAlert(
                ID='PASTAL', parent_id='P1', student_id='S1',
                subject_id='SUB1', semester_id='PAST', event_id='PASTEV',
                alert_type='attention', average=42
            )
        ])
        self.session.commit()

        admin_module = importlib.import_module('admin.Admin')
        previous_factory = admin_module.Session
        admin_module.Session = sessionmaker(bind=self.engine)
        try:
            admin_module.publish_expired_semesters()
        finally:
            admin_module.Session = previous_factory

        report = self.session.query(SemesterGradeReport).filter_by(
            semester_id='PAST'
        ).one()
        semester = self.session.query(Semester).filter_by(ID='PAST').one()
        self.assertEqual(report.average, 42)
        self.assertEqual(report.attention_count, 1)
        self.assertIsNotNone(semester.closed_at)


if __name__ == '__main__':
    unittest.main()
