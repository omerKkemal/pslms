import unittest

from sqlalchemy import create_engine, inspect

from database.manage_db import create_grade_reporting_tables


class DatabaseSchemaMigrationTests(unittest.TestCase):
    def test_existing_parent_table_gets_password_column_without_losing_rows(self):
        engine = create_engine('sqlite:///:memory:')
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql(
                    'CREATE TABLE student (id VARCHAR PRIMARY KEY)'
                )
                connection.exec_driver_sql(
                    'CREATE TABLE parent ('
                    'id VARCHAR PRIMARY KEY, '
                    'student_id VARCHAR, '
                    'hous_number INTEGER, '
                    'fname VARCHAR NOT NULL, '
                    'lname VARCHAR NOT NULL, '
                    'phone INTEGER, '
                    'email INTEGER)'
                )
                connection.exec_driver_sql(
                    "INSERT INTO student (id) VALUES ('S1')"
                )
                connection.exec_driver_sql(
                    "INSERT INTO parent (id, student_id, hous_number, fname, lname) "
                    "VALUES ('P1', 'S1', 42, 'Ava', 'Parent')"
                )
                connection.exec_driver_sql(
                    'CREATE TABLE rank ('
                    'id VARCHAR PRIMARY KEY, '
                    'student_id VARCHAR NOT NULL, '
                    'rank INTEGER NOT NULL, '
                    'simister FLOAT NOT NULL)'
                )
                connection.exec_driver_sql(
                    'CREATE TABLE parent_grade_alert ('
                    'id VARCHAR PRIMARY KEY, '
                    'parent_id VARCHAR NOT NULL, '
                    'student_id VARCHAR NOT NULL, '
                    'subject_id VARCHAR NOT NULL, '
                    'event_id VARCHAR NOT NULL, '
                    'alert_type VARCHAR(20) NOT NULL, '
                    'average FLOAT NOT NULL, '
                    'previous_average FLOAT, '
                    'created_at DATETIME NOT NULL)'
                )
                connection.exec_driver_sql(
                    "INSERT INTO rank (id, student_id, rank, simister) "
                    "VALUES ('R1', 'S1', 2, 1.0)"
                )
                connection.exec_driver_sql(
                    "INSERT INTO parent_grade_alert "
                    "(id, parent_id, student_id, subject_id, event_id, alert_type, average, created_at) "
                    "VALUES ('A1', 'P1', 'S1', 'SUB1', 'E1', 'attention', 40, CURRENT_TIMESTAMP)"
                )

            create_grade_reporting_tables(engine)

            columns = {
                column['name'] for column in inspect(engine).get_columns('parent')
            }
            rank_columns = {
                column['name'] for column in inspect(engine).get_columns('rank')
            }
            alert_columns = {
                column['name']
                for column in inspect(engine).get_columns('parent_grade_alert')
            }
            with engine.connect() as connection:
                parent = connection.exec_driver_sql(
                    "SELECT id, fname, lname, password FROM parent WHERE id = 'P1'"
                ).one()
                old_rank = connection.exec_driver_sql(
                    "SELECT id, student_id, rank, semester_id FROM rank WHERE id = 'R1'"
                ).one()
                parent_student = connection.exec_driver_sql(
                    "SELECT parent_id, student_id FROM parent_student"
                ).one()
                old_alert = connection.exec_driver_sql(
                    "SELECT id, assessment_name, semester_id "
                    "FROM parent_grade_alert WHERE id = 'A1'"
                ).one()

            self.assertIn('password', columns)
            self.assertEqual(parent, ('P1', 'Ava', 'Parent', None))
            self.assertEqual(parent_student, ('P1', 'S1'))
            self.assertIn('assessment_name', alert_columns)
            self.assertEqual(old_alert, ('A1', None, None))
            self.assertIn('semester_id', rank_columns)
            self.assertEqual(old_rank, ('R1', 'S1', 2, None))
        finally:
            engine.dispose()


if __name__ == '__main__':
    unittest.main()
