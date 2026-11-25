import importlib
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.modle import (
    Assessment, AssessmentDeadline, Base, CreatAssessment, Parent,
    ParentGradeAlert, ParentStudent, Semester, Student, Subjects, Teacher,
    thought
)


class TeacherMissingAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.teacher_module = importlib.import_module('teacher.Teacher')
        self.previous_factory = self.teacher_module.Session
        self.teacher_module.Session = sessionmaker(bind=self.engine)
        self.application_module = importlib.import_module('app')
        self.client = self.application_module.app.test_client()

        today = date.today()
        now = datetime.now()
        self.session.add_all([
            Teacher('T1', 'Taylor', 'Middle', 'Teacher', 'F', 'password'),
            Student('S1', 'Ava', '', 'Learner', 'F', 'password', 'A', 1),
            Student('S2', 'Ben', '', 'Learner', 'M', 'password', 'A', 1),
            Subjects('MATH', 'Math', 'ReadOnly'),
            Semester(
                ID='TERM',
                name='Current Term',
                starts_on=today - timedelta(days=10),
                ends_on=today + timedelta(days=10)
            ),
            thought('TH1', 'MATH', 'T1', '1', 'A', 'Read&Write'),
            CreatAssessment('MID', 'Midterm Exam', 'T1', 20),
            AssessmentDeadline(
                assessment_type='midterm',
                due_at=now - timedelta(days=1)
            ),
            AssessmentDeadline(
                assessment_type='final',
                due_at=now + timedelta(days=10)
            ),
            Assessment(
                'A1', 'S1', 'T1', 'MATH', '1', 'A', 'Midterm Exam', 15, 'TERM'
            )
        ])
        self.session.commit()

    def tearDown(self):
        self.teacher_module.Session = self.previous_factory
        self.session.close()
        self.engine.dispose()

    def _login_as_teacher(self):
        with self.client.session_transaction() as browser_session:
            browser_session.update(
                userID='T1',
                role='teacher',
                username='Taylor Teacher',
                _user_id='T1',
                _fresh=True
            )

    def test_class_page_shows_specific_missing_assessment_and_score_form(self):
        self._login_as_teacher()
        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.get('/teacher/class/1/A/MATH')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Missing assessment grades (NG)', response.data)
        self.assertIn(b'Ben Learner (S2)', response.data)
        self.assertIn(b'Midterm Exam', response.data)
        self.assertIn(b'Record grade', response.data)
        self.assertIn(b'Update', response.data)
        self.assertIn(b'max="20.0"', response.data)
        self.assertIn(b'value="15.0"', response.data)
        self.assertIn(b'<select name="assessment_name" required', response.data)
        self.assertIn(
            b'value="Midterm Exam" data-max="20.0">Midterm Exam (out of 20.0)</option>',
            response.data
        )
        self.assertNotIn(b'Calculate Ranks', response.data)

    def test_class_page_tells_teacher_to_contact_admin_without_active_semester(self):
        self.session.query(Semester).delete()
        self.session.commit()
        self._login_as_teacher()

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.get('/teacher/class/1/A/MATH')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No active semester is configured.', response.data)
        self.assertIn(b'Please contact your administrator.', response.data)

    def test_teacher_can_record_and_update_the_missing_assessment_score(self):
        self._login_as_teacher()
        form_data = {
            'student_id': 'S2',
            'subject_id': 'MATH',
            'grade': '1',
            'section': 'A',
            'semester_id': 'TERM',
            'assessment_name': 'Midterm Exam',
            'score': '18'
        }
        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post('/teacher/grade/submit', data=form_data)
        self.assertEqual(response.status_code, 302)

        record = self.session.query(Assessment).filter_by(
            student_id='S2', semester_id='TERM'
        ).one()
        self.assertEqual(record.ScoreMark, 18)

        form_data['score'] = '19'
        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post('/teacher/grade/submit', data=form_data)
        self.assertEqual(response.status_code, 302)

        self.session.expire_all()
        records = self.session.query(Assessment).filter_by(
            student_id='S2', semester_id='TERM'
        ).all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].ScoreMark, 19)

    def test_parent_gets_low_assessment_alert_and_recovery(self):
        self.session.add_all([
            Parent('P2', 'Ava', 'Guardian', student_id='S2', hous_number=12),
            ParentStudent('P2', 'S2')
        ])
        self.session.commit()
        self._login_as_teacher()
        form_data = {
            'student_id': 'S2',
            'subject_id': 'MATH',
            'grade': '1',
            'section': 'A',
            'semester_id': 'TERM',
            'assessment_name': 'Midterm Exam',
            'score': '9'
        }

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post('/teacher/grade/submit', data=form_data)
        self.assertEqual(response.status_code, 302)

        alert = self.session.query(ParentGradeAlert).one()
        self.assertEqual(alert.parent_id, 'P2')
        self.assertEqual(alert.alert_type, 'assessment_attention')
        self.assertEqual(alert.assessment_name, 'Midterm Exam')
        self.assertEqual(alert.average, 45)

        with patch.object(self.application_module, 'publish_expired_semesters'):
            self.client.post('/teacher/grade/submit', data=form_data)
        self.assertEqual(self.session.query(ParentGradeAlert).count(), 1)

        form_data['score'] = '12'
        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post('/teacher/grade/submit', data=form_data)
        self.assertEqual(response.status_code, 302)

        alerts = self.session.query(ParentGradeAlert).order_by(
            ParentGradeAlert.created_at
        ).all()
        self.assertEqual(
            [alert.alert_type for alert in alerts],
            ['assessment_attention', 'assessment_recovery']
        )
        self.assertEqual(alerts[1].average, 60)
        self.assertEqual(alerts[1].previous_average, 45)

    def test_teacher_cannot_write_to_a_read_only_class(self):
        assignment = self.session.query(thought).filter_by(ID='TH1').one()
        assignment.access_level = 'ReadOnly'
        self.session.commit()
        self._login_as_teacher()

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post('/teacher/grade/submit', data={
                'student_id': 'S2',
                'subject_id': 'MATH',
                'grade': '1',
                'section': 'A',
                'semester_id': 'TERM',
                'assessment_name': 'Midterm Exam',
                'score': '18'
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.session.query(Assessment).filter_by(student_id='S2').count(),
            0
        )

    def test_teacher_cannot_submit_an_assessment_they_did_not_create(self):
        self._login_as_teacher()

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post('/teacher/grade/submit', data={
                'student_id': 'S2',
                'subject_id': 'MATH',
                'grade': '1',
                'section': 'A',
                'semester_id': 'TERM',
                'assessment_name': 'Uncreated Quiz',
                'score': '8'
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.session.query(Assessment).filter_by(student_id='S2').count(),
            0
        )


if __name__ == '__main__':
    unittest.main()
