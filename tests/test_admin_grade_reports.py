import importlib
import unittest
from datetime import date, datetime
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.modle import (
    Assessment, Base, CreatAssessment, Parent, ParentGradeAlert, rank,
    Semester, SemesterSubjectAverage, Student, Subjects, Teacher,
    YearlySubjectGradeReport
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
        self.assertIn(b'Calculate ranks for Grade 1 / Section A', response.data)

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

    def test_yearly_report_averages_two_terms_and_omits_incomplete_subjects(self):
        semester1 = Semester(
            ID='YEAR1',
            name='Semester 1',
            starts_on=date(2025, 1, 1),
            ends_on=date(2025, 5, 31),
            closed_at=datetime(2025, 6, 1)
        )
        semester2 = Semester(
            ID='YEAR2',
            name='Semester 2',
            starts_on=date(2025, 6, 1),
            ends_on=date(2025, 10, 31),
            closed_at=datetime(2025, 11, 1)
        )
        self.session.add_all([
            semester1,
            semester2,
            SemesterSubjectAverage(
                ID='YAVG1', semester_id='YEAR1', student_id='S1',
                subject_id='MATH', average=80
            ),
            SemesterSubjectAverage(
                ID='YAVG2', semester_id='YEAR2', student_id='S1',
                subject_id='MATH', average=90
            ),
            SemesterSubjectAverage(
                ID='YAVG3', semester_id='YEAR1', student_id='S1',
                subject_id='SCI', average=70
            )
        ])
        self.session.commit()
        self._login_as('admin')

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post(
                '/admin/reports/calculate-yearly',
                data={
                    'year': '2025',
                    'semester1_id': 'YEAR1',
                    'semester2_id': 'YEAR2'
                }
            )

        self.assertEqual(response.status_code, 302)
        report_rows = self.session.query(YearlySubjectGradeReport).filter_by(
            year=2025
        ).all()
        self.assertEqual(len(report_rows), 1)
        self.assertEqual(report_rows[0].subject_id, 'MATH')
        self.assertEqual(report_rows[0].semester1_average, 80)
        self.assertEqual(report_rows[0].semester2_average, 90)
        self.assertEqual(report_rows[0].annual_average, 85)

        self.session.query(SemesterSubjectAverage).filter_by(
            ID='YAVG2'
        ).one().average = 92
        self.session.commit()
        with patch.object(self.application_module, 'publish_expired_semesters'):
            self.client.post(
                '/admin/reports/calculate-yearly',
                data={
                    'year': '2025',
                    'semester1_id': 'YEAR1',
                    'semester2_id': 'YEAR2'
                }
            )
        self.session.expire_all()
        refreshed_reports = self.session.query(YearlySubjectGradeReport).filter_by(
            year=2025
        ).all()
        self.assertEqual(len(refreshed_reports), 1)
        self.assertEqual(refreshed_reports[0].annual_average, 86)

        with patch.object(self.application_module, 'publish_expired_semesters'):
            report_page = self.client.get('/admin/reports?semester_id=YEAR2')
        self.assertEqual(report_page.status_code, 200)
        self.assertIn(b'2025 Annual Grade Report', report_page.data)
        self.assertIn(b'86.0%', report_page.data)

    def test_yearly_report_calculation_is_admin_only(self):
        self._login_as('teacher')

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post(
                '/admin/reports/calculate-yearly',
                data={
                    'year': '2025',
                    'semester1_id': 'YEAR1',
                    'semester2_id': 'YEAR2'
                }
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.session.query(YearlySubjectGradeReport).count(), 0)

    def test_teacher_class_list_has_no_rank_action(self):
        from database.modle import thought

        self.session.add(thought(
            'TH-CLASS', 'MATH', 'T1', '1', 'A', 'Read&Write'
        ))
        self.session.commit()
        self._login_as('teacher')

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.get('/teacher/classes')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Calc Ranks', response.data)
        self.assertNotIn(b'/teacher/calculate_ranks/', response.data)
        with patch.object(self.application_module, 'publish_expired_semesters'):
            removed_route = self.client.get('/teacher/calculate_ranks/1/A')
        self.assertEqual(removed_route.status_code, 404)


if __name__ == '__main__':
    unittest.main()
