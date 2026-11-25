import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.modle import Base, Parent, ParentStudent, Student


class AdminParentDeduplicationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.admin_module = importlib.import_module('admin.Admin')
        self.previous_session = self.admin_module._session
        self.admin_module._session = self.session
        self.application_module = importlib.import_module('app')
        self.client = self.application_module.app.test_client()
        with self.client.session_transaction() as browser_session:
            browser_session.update(
                userID='ADMIN1',
                role='admin',
                username='Admin',
                _user_id='ADMIN1',
                _fresh=True
            )

    def tearDown(self):
        self.admin_module._session = self.previous_session
        self.session.close()
        self.engine.dispose()

    def _post_add_student(self, data):
        permanent = SimpleNamespace(Gender={'male': 'M', 'female': 'F'})
        with patch.object(self.application_module, 'publish_expired_semesters'):
            with patch.object(
                self.admin_module,
                'read_from_json',
                return_value=(SimpleNamespace(Permanent=permanent), {})
            ):
                return self.client.post(
                    '/admin/panal/add_student/1/A',
                    data=data
                )

    def test_house_number_is_required_when_adding_student(self):
        response = self._post_add_student({
            'fname': 'Ava',
            'mname': 'Jane',
            'lname': 'Doe',
            'gender': 'F'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.session.query(Student).count(), 0)
        self.assertEqual(self.session.query(Parent).count(), 0)

    def test_add_student_reuses_matching_parent_and_links_new_student(self):
        self.session.add_all([
            Student('S1', 'Ben', 'M', 'Doe', 'M', 'password', 'A', 1),
            Parent(
                'P1', 'Jane', 'Doe', student_id='S1', hous_number=42
            ),
            ParentStudent('P1', 'S1')
        ])
        self.session.commit()

        response = self._post_add_student({
            'fname': 'Ava',
            'mname': ' JANE ',
            'lname': 'DOE',
            'gender': 'F',
            'parent_hous_number': '42'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.session.query(Parent).count(), 1)
        new_student = self.session.query(Student).filter_by(fname='Ava').one()
        self.assertIsNotNone(self.session.query(ParentStudent).filter_by(
            parent_id='P1',
            student_id=new_student.ID
        ).first())
        parent_module = importlib.import_module('parent.Parent')
        children = parent_module._get_parent_children(
            self.session,
            self.session.query(Parent).filter_by(ID='P1').one()
        )
        self.assertEqual({student.ID for student in children}, {'S1', new_student.ID})

    def test_dashboard_add_student_also_requires_house_number(self):
        permanent = SimpleNamespace(Gender={'male': 'M', 'female': 'F'})
        with patch.object(self.application_module, 'publish_expired_semesters'):
            with patch.object(
                self.admin_module,
                'read_from_json',
                return_value=(SimpleNamespace(Permanent=permanent), {})
            ):
                response = self.client.post(
                    '/admin/panal/add_students',
                    data={
                        'fname': 'Ava',
                        'mname': 'Jane',
                        'lname': 'Doe',
                        'gender': 'F',
                        'grade': '1',
                        'section': 'A'
                    }
                )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.session.query(Student).count(), 0)
        self.assertEqual(self.session.query(Parent).count(), 0)

    def test_manual_parent_add_requires_house_number_and_reuses_match(self):
        self.session.add_all([
            Student('S1', 'Ava', 'M', 'Doe', 'F', 'password', 'A', 1),
            Student('S2', 'Ben', 'M', 'Doe', 'M', 'password', 'A', 1),
            Parent(
                'P1', 'Jane', 'Doe', student_id='S1', hous_number=42
            ),
            ParentStudent('P1', 'S1')
        ])
        self.session.commit()

        with patch.object(self.application_module, 'publish_expired_semesters'):
            missing_house_response = self.client.post(
                '/admin/panal/add_parent',
                data={'fname': 'Jane', 'lname': 'Doe', 'student_id': 'S2'}
            )
        self.assertEqual(missing_house_response.status_code, 302)
        self.assertEqual(self.session.query(Parent).count(), 1)

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post(
                '/admin/panal/add_parent',
                data={
                    'fname': ' JANE ',
                    'lname': 'DOE',
                    'hous_number': '42',
                    'student_id': 'S2'
                }
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.session.query(Parent).count(), 1)
        self.assertIsNotNone(self.session.query(ParentStudent).filter_by(
            parent_id='P1',
            student_id='S2'
        ).first())

    def test_update_parent_info_edits_fields_and_rejects_duplicate_identity(self):
        self.session.add_all([
            Parent(
                'P1', 'Jane', 'Doe', hous_number=42,
                email='old@example.com', phone='111'
            ),
            Parent(
                'P2', 'Alex', 'Smith', hous_number=15
            )
        ])
        self.session.commit()

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post(
                '/admin/panal/update_parent/P1',
                data={
                    'fname': 'Jane',
                    'lname': 'Doe',
                    'hous_number': '43',
                    'email': 'new@example.com',
                    'phone': '222'
                }
            )
        self.assertEqual(response.status_code, 302)
        updated_parent = self.session.query(Parent).filter_by(ID='P1').one()
        self.assertEqual(updated_parent.hous_number, 43)
        self.assertEqual(updated_parent.email, 'new@example.com')
        self.assertEqual(updated_parent.phone, '222')

        with patch.object(self.application_module, 'publish_expired_semesters'):
            duplicate_response = self.client.post(
                '/admin/panal/update_parent/P1',
                data={
                    'fname': ' alex ',
                    'lname': 'SMITH',
                    'hous_number': '15',
                    'email': 'duplicate@example.com',
                    'phone': '333'
                }
            )

        self.assertEqual(duplicate_response.status_code, 302)
        self.session.expire_all()
        unchanged_parent = self.session.query(Parent).filter_by(ID='P1').one()
        self.assertEqual(unchanged_parent.fname, 'Jane')
        self.assertEqual(unchanged_parent.hous_number, 43)

    def test_parent_list_renders_update_info_button(self):
        self.session.add(Parent(
            'P1', 'Jane', 'Doe', hous_number=42
        ))
        self.session.commit()

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.get('/admin/panal/get_parents')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Update Info', response.data)
        self.assertIn(b'/admin/panal/update_parent/P1', response.data)


if __name__ == '__main__':
    unittest.main()
