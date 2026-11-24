import io
import tempfile
import unittest
import importlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import app
from database.modle import Admin, Base, Resource, Sections


class AdminResourceUploadTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        session = self.session_factory()
        session.add(Admin('ADMIN1', 'admin', 'password'))
        session.commit()
        session.close()

        self.admin_module = importlib.import_module('admin.Admin')
        self.previous_session = self.admin_module._session
        self.previous_factory = self.admin_module.Session
        self.admin_module._session = self.session_factory()
        self.admin_module.Session = self.session_factory
        self.client = app.test_client()
        with self.client.session_transaction() as browser_session:
            browser_session.update(
                userID='ADMIN1',
                role='admin',
                username='Admin',
                _user_id='ADMIN1',
                _fresh=True
            )

    def tearDown(self):
        self.admin_module._session.close()
        self.admin_module._session = self.previous_session
        self.admin_module.Session = self.previous_factory
        self.engine.dispose()

    def test_admin_upload_uses_configured_types_and_memory_section_values(self):
        response = self.client.get('/admin/panal/add_resource')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Assignment', response.data)
        self.assertIn(b'Worksheet', response.data)
        self.assertNotIn(b'extra books', response.data)
        self.assertIn(b'value="A"', response.data)

        response = self.client.get('/view_resource')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Assignment', response.data)
        self.assertIn(b'Worksheet', response.data)
        self.assertNotIn(b'extra books', response.data)
        self.assertIn(b'value="A"', response.data)

        original_path = self.admin_module.var.WORK_SHEET_PATH
        original_link = self.admin_module.var.WORK_SHEET_LINK_PATH
        try:
            with tempfile.TemporaryDirectory() as upload_dir:
                self.admin_module.var.WORK_SHEET_PATH = upload_dir
                self.admin_module.var.WORK_SHEET_LINK_PATH = 'uploads'
                response = self.client.post(
                    '/admin/panal/add_resource',
                    data={
                        'description': 'Practice work',
                        'resource_type': 'work sheet',
                        'grade': '1',
                        'section': 'A',
                        'files': (io.BytesIO(b'resource test'), 'practice.pdf')
                    },
                    content_type='multipart/form-data'
                )
                self.assertEqual(response.status_code, 302)
                session = self.session_factory()
                resource = session.query(Resource).one()
                section = session.query(Sections).filter_by(
                    ID=resource.section_id
                ).one()
                self.assertEqual((section.grade, section.section), (1, 'A'))
                session.close()
        finally:
            self.admin_module.var.WORK_SHEET_PATH = original_path
            self.admin_module.var.WORK_SHEET_LINK_PATH = original_link


if __name__ == '__main__':
    unittest.main()
