import importlib
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from openpyxl import Workbook, load_workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.modle import Base, Parent, ParentStudent, Sections, Student


class AdminExcelStudentImportTests(unittest.TestCase):
    HEADERS = [
        'first_name',
        'middle_name',
        'last_name',
        'gender',
        'grade',
        'section',
        'parent_house_number',
        'parent_phone',
        'parent_email'
    ]

    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.admin_module = importlib.import_module('admin.Admin')
        self.previous_session = self.admin_module._session
        self.admin_module._session = self.session
        self.application_module = importlib.import_module('app')
        self.client = self.application_module.app.test_client()
        self.school_data = SimpleNamespace(Permanent=SimpleNamespace(
            Gender={'male': 'M', 'female': 'F'},
            grade=[1, 2],
            section=['A', 'B']
        ))
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

    def _workbook_bytes(self, headers=None, rows=()):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.append(headers or self.HEADERS)
        for row in rows:
            worksheet.append(row)
        output = BytesIO()
        workbook.save(output)
        return output.getvalue()

    def _upload(self, workbook_bytes, filename='students.xlsx'):
        with patch.object(self.application_module, 'publish_expired_semesters'):
            with patch.object(
                self.admin_module,
                'read_from_json',
                return_value=(self.school_data, {})
            ):
                return self.client.post(
                    '/admin/panal/students/import',
                    data={
                        'students_file': (BytesIO(workbook_bytes), filename)
                    },
                    content_type='multipart/form-data',
                    follow_redirects=True
                )

    def test_import_adds_students_and_reuses_matching_parent(self):
        rows = [
            ['Ava', 'Jordan', 'Parent', 'Female', 1, 'A', 42, '5550100', 'a@example.com'],
            ['Ben', 'Jordan', 'Parent', 'M', 1, 'A', 42, '5550100', 'a@example.com']
        ]

        response = self._upload(self._workbook_bytes(rows=rows))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.query(Student).count(), 2)
        self.assertEqual(self.session.query(Parent).count(), 1)
        self.assertEqual(self.session.query(ParentStudent).count(), 2)
        self.assertEqual(self.session.query(Sections).filter_by(
            grade=1, section='A'
        ).count(), 1)

    def test_import_skips_duplicate_students_in_file(self):
        row = ['Ava', 'Jordan', 'Parent', 'Female', 1, 'A', 42, '', '']

        response = self._upload(self._workbook_bytes(rows=[row, row]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.query(Student).count(), 1)
        self.assertIn(b'1 duplicate row(s) skipped', response.data)

    def test_invalid_row_cancels_the_entire_import(self):
        rows = [
            ['Ava', 'Jordan', 'Parent', 'Female', 1, 'A', 42, '', ''],
            ['Ben', 'Jordan', 'Parent', 'Unknown', 1, 'A', 42, '', '']
        ]

        response = self._upload(self._workbook_bytes(rows=rows))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.query(Student).count(), 0)
        self.assertEqual(self.session.query(Parent).count(), 0)
        self.assertIn(b'Row 3: Gender must be Male or Female', response.data)

    def test_import_requires_house_number_and_all_required_headers(self):
        row_without_house = ['Ava', 'Jordan', 'Parent', 'F', 1, 'A', None, '', '']
        response = self._upload(self._workbook_bytes(rows=[row_without_house]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.query(Student).count(), 0)
        self.assertIn(b'Parent house number must be a whole number', response.data)

        response = self._upload(self._workbook_bytes(
            headers=['first_name', 'last_name'],
            rows=[['Ava', 'Parent']]
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.query(Student).count(), 0)
        self.assertIn(b'Missing required columns', response.data)

    def test_import_rejects_non_xlsx_workbooks(self):
        response = self._upload(self._workbook_bytes(), filename='students.xls')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.query(Student).count(), 0)
        self.assertIn(b'must be Excel .xlsx files', response.data)

    def test_import_reports_corrupt_xlsx_without_creating_records(self):
        response = self._upload(b'not an excel workbook')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.query(Student).count(), 0)
        self.assertIn(b'Could not read the workbook', response.data)

    def test_template_download_contains_required_import_headers(self):
        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.get('/admin/panal/students/import-template')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.mimetype,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        workbook = load_workbook(BytesIO(response.data), read_only=True)
        headers = list(next(workbook.worksheets[0].iter_rows(values_only=True)))
        self.assertEqual(headers, self.HEADERS)
        workbook.close()

    def test_admin_panel_offers_import_form_and_template(self):
        with patch.object(self.application_module, 'publish_expired_semesters'):
            with patch.object(
                self.admin_module,
                'read_from_json',
                return_value=(self.school_data, {})
            ):
                response = self.client.get('/admin/panal')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Import Students from Excel', response.data)
        self.assertIn(b'enctype="multipart/form-data"', response.data)
        self.assertIn(b'Download Excel template', response.data)

    def test_teacher_cannot_import_students(self):
        with self.client.session_transaction() as browser_session:
            browser_session['role'] = 'teacher'
            browser_session['userID'] = 'T1'
            browser_session['_user_id'] = 'T1'

        with patch.object(self.application_module, 'publish_expired_semesters'):
            response = self.client.post(
                '/admin/panal/students/import',
                data={'students_file': (BytesIO(self._workbook_bytes()), 'students.xlsx')},
                content_type='multipart/form-data'
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.session.query(Student).count(), 0)


if __name__ == '__main__':
    unittest.main()
