import importlib
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.modle import AssessmentDeadline, Base, Semester


class AdminSystemNoticesTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.admin_module = importlib.import_module('admin.Admin')
        self.previous_session = self.admin_module._session
        self.admin_module._session = self.session

    def tearDown(self):
        self.admin_module._session = self.previous_session
        self.session.close()
        self.engine.dispose()

    def test_notices_reflect_active_semester_and_upcoming_deadline(self):
        today = date(2026, 3, 10)
        now = datetime(2026, 3, 10, 9)
        self.session.add_all([
            Semester(
                ID='SPRING',
                name='Spring Term',
                starts_on=today - timedelta(days=10),
                ends_on=today + timedelta(days=20)
            ),
            AssessmentDeadline(
                assessment_type='midterm',
                due_at=now + timedelta(days=2)
            )
        ])
        self.session.commit()

        with patch.object(self.admin_module, '_collect_attention_items', return_value=[]):
            notices = self.admin_module._collect_system_notices(today, now)

        self.assertEqual(notices[0]['title'], 'Active semester')
        self.assertIn('Spring Term', notices[0]['message'])
        self.assertEqual(notices[1]['title'], 'Midterm deadline approaching')
        self.assertIn('March 12, 2026', notices[1]['message'])

    def test_overdue_deadline_reports_actual_missing_grade_count(self):
        now = datetime(2026, 3, 10, 9)
        self.session.add(AssessmentDeadline(
            assessment_type='final',
            due_at=now - timedelta(days=1)
        ))
        self.session.commit()
        attention_items = [{
            'kind': 'final',
            'students': [object(), object()]
        }]

        with patch.object(
            self.admin_module,
            '_collect_attention_items',
            return_value=attention_items
        ):
            notices = self.admin_module._collect_system_notices(
                date(2026, 3, 10), now
            )

        overdue_notice = next(
            notice for notice in notices
            if notice['title'] == 'Missing final grades'
        )
        self.assertIn('2 students', overdue_notice['message'])

    def test_no_semester_notice_appears_when_no_term_is_configured(self):
        with patch.object(self.admin_module, '_collect_attention_items', return_value=[]):
            notices = self.admin_module._collect_system_notices(
                date(2026, 3, 10), datetime(2026, 3, 10, 9)
            )

        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]['title'], 'No active semester')
        self.assertNotIn('backup', notices[0]['message'].lower())

    def test_dashboard_renders_generated_notices_without_an_admin_notice_form(self):
        today = date.today()
        self.session.add(Semester(
            ID='CURRENT',
            name='Current Term',
            starts_on=today - timedelta(days=1),
            ends_on=today + timedelta(days=20)
        ))
        self.session.commit()
        application_module = importlib.import_module('app')
        client = application_module.app.test_client()
        with client.session_transaction() as browser_session:
            browser_session.update(
                userID='ADMIN1',
                role='admin',
                username='Admin',
                _user_id='ADMIN1',
                _fresh=True
            )

        with patch.object(application_module, 'publish_expired_semesters'):
            with patch.object(self.admin_module, '_collect_attention_items', return_value=[]):
                response = client.get('/admin/Dashboard')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Current Term is active through', response.data)
        self.assertNotIn(b'Publish Notice', response.data)
        self.assertNotIn(b'Server backup due tonight', response.data)


if __name__ == '__main__':
    unittest.main()
