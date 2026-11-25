import importlib
import unittest
from datetime import date, datetime
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.modle import (
    Assessment, Base, CreatAssessment, Parent, ParentGradeAlert, rank,
    Semester, SemesterSubjectAverage, Student, Subjects, Teacher
)


class AdminGradeReportTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.admin_module = importlib.import_module('admin.Admin')
        self.previous_session = self.admin_module._session
        self.admin_module._session = self.session
        self.application_module = importlib.import_module('app')
        self.client = self.application_module.app.test_client()
        self.semester = Semester(
            ID='TERM',
            name='Spring Term',
            starts_on=date(2026, 1, 1),
            ends_on=date(2026, 12, 31)
        )
        self.students = [
            Student('S1', 'Ava', '', 'Learner', 'F', 'password', 'A', 1),
            Student('S2', 'Ben', '', 'Learner', 'M', 'password', 'B', 1),
            Student('S3', 'Cam', '', 'Learner', 'F', 'password', 'A', 1)
        ]
        self.session.add_all([
            self.semester,
            *self.students,
            Teacher('T1', 'Taylor', 'Middle', 'Teacher', 'F', 'password'),
            Subjects('MATH', 'Math', 'ReadOnly'),
            Subjects('SCI', 'Science', 'ReadOnly'),
            CreatAssessment('MID', 'Midterm Exam', 'T1', 20),
            CreatAssessment('FIN', 'Final Exam', 'T1', 40),
            Parent('P1', 'Parent', 'One', student_id='S1', hous_number=15),
            Parent('P2', 'Parent', 'Two', student_id='S1', hous_number=15),
            Assessment('A1', 'S1', 'T1', 'MATH', '1', 'A', 'Midterm Exam', 15, 'TERM'),
            Assessment('A2', 'S1', 'T1', 'MATH', '1', 'A', 'Final Exam', 33, 'TERM'),
            Assessment('A3', 'S2', 'T1', 'MATH', '1', 'B', 'Final Exam', 30, 'TERM'),
            SemesterSubjectAverage(
                ID='AVG1', semester_id='TERM', student_id='S1',
                subject_id='MATH', average=80
            ),
            SemesterSubjectAverage(
                ID='AVG2', semester_id='TERM', student_id='S1',
                subject_id='SCI', average=100
            ),
            SemesterSubjectAverage(
                ID='AVG3', semester_id='TERM', student_id='S2',
                subject_id='MATH', average=75
            ),
            SemesterSubjectAverage(
                ID='AVG4', semester_id='TERM', student_id='S3',
                subject_id='MATH', average=95
            ),
            ParentGradeAlert(
                ID='AL1', parent_id='P1', student_id='S1', subject_id='MATH',
                semester_id='TERM', event_id='EV1', alert_type='attention',
                average=40, previous_average=None,
                created_at=datetime(2026, 3, 1, 9)
            ),
            ParentGradeAlert(
                ID='AL2', parent_id='P2', student_id='S1', subject_id='MATH',
                semester_id='TERM', event_id='EV1', alert_type='attention',
                average=40, previous_average=None,
                created_at=datetime(2026, 3, 1, 9)
            ),
            ParentGradeAlert(
                ID='AL3', parent_id='P1', student_id='S1', subject_id='MATH',
                semester_id='TERM', event_id='EV2', alert_type='improvement',
                average=55, previous_average=40,
                created_at=datetime(2026, 3, 5, 9)
            ),
            ParentGradeAlert(
                ID='AL4', parent_id='P2', student_id='S1', subject_id='MATH',
                semester_id='TERM', event_id='EV2', alert_type='improvement',
                average=55, previous_average=40,
                created_at=datetime(2026, 3, 5, 9)
            )
        ])
        self.session.commit()

    def tearDown(self):
        self.admin_module._session = self.previous_session
        self.session.close()
        self.engine.dispose()

    def _login_as(self, role):
        with self.client.session_transaction() as browser_session:
            browser_session.update(
                userID='ADMIN1' if role == 'admin' else 'T1',
                role=role,
                username='Admin' if role == 'admin' else 'Teacher',
                _user_id='ADMIN1' if role == 'admin' else 'T1',
                _fresh=True
            )

    def test_report_filters_grade_section_semester_and_assessment_type(self):
        self._login_as('admin')
        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.get(
                '/admin/reports?semester_id=TERM&grade=1&section=A&assessment_type=midterm'
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ava Learner', response.data)
        self.assertNotIn(b'Ben Learner', response.data)
        self.assertNotIn(b'Cam Learner', response.data)

    def test_report_card_includes_all_scores_notice_counts_and_later_improvement(self):
        self._login_as('admin')
        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.get(
                '/admin/reports/student/S1?semester_id=TERM'
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Midterm Exam', response.data)
        self.assertIn(b'Final Exam', response.data)
        self.assertIn(b'15.0 / 20.0', response.data)
        self.assertIn(b'33.0 / 40.0', response.data)
        self.assertIn(b'Improved afterward to 55.0%', response.data)
        self.assertEqual(response.data.count(b'2 notice events recorded'), 2)

    def test_only_admin_can_calculate_class_ranks_for_a_semester(self):
        self._login_as('teacher')
        form_data = {
            'semester_id': 'TERM',
            'grade': '1',
            'section': 'A'
        }
        with patch.object(self.application_module, 'publish_expired_semesters'):
            denied_response = self.client.post(
                '/admin/reports/calculate-ranks', data=form_data
            )
        self.assertEqual(denied_response.status_code, 302)
        self.assertEqual(self.session.query(rank).count(), 0)

        self._login_as('admin')
        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post(
                '/admin/reports/calculate-ranks', data=form_data
            )

        self.assertEqual(response.status_code, 302)
        calculated_ranks = {
            entry.student_id: entry.rank
            for entry in self.session.query(rank).filter_by(
                semester_id='TERM'
            ).all()
        }
        self.assertEqual(calculated_ranks, {'S1': 2, 'S3': 1})


if __name__ == '__main__':
    unittest.main()
