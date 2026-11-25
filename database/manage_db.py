# =========================================================================== #
# Author: Omer Kemal                                                          #
# Website: https://www.johndoe.com                                            #
# Social Media:                                                               #
#   - Facebook: https://www.facebook.com/johndoe                              #
#   - Telegram: https://t.me/johndoe                                          #
#   - Twitter: @JohnDoe                                                       #
#   - GitHub: https://github.com/johndoe                                      #
# =========================================================================== #

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect

from database.modle import (
    Base, Admin, Subjects, ParentStudent, ParentGradeAlert, Semester,
    SemesterSubjectAverage, SemesterGradeReport
)
from utility.setting import Setting

# Initialize settings and set variables
var = Setting()
var.setting_var()


# Ensure the database directory exists
def create_db_dir():
    db_dir = var.DB_DIR
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        return 'db directory has been created ^_^'
    else:
        return 'db directory already exist ^_^'


# Ensure the log directory exists
def create_log_dir():
    log_dir = var.LOG_DIR
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        return 'log directory has been created ^_^'
    else:
        return 'log directory already exist ^_^'


# Ensure the excel directory exists
def create_excel_dir():
    excel_dir = var.EXCEL_DIR
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)
        return 'execl directory has been created ^_^'
    else:
        return 'execl directory already exist ^_^'


# Create the engine using the database URI from settings
def _create_engine():
    return create_engine(var.DB_URI)

engine = _create_engine()


# Create all tables defined in the models (if they don't exist yet)
def create_all_db_tables(_engine):
    Base.metadata.create_all(_engine)
    return 'database was created successfully along with the table'


def create_grade_reporting_tables(_engine):
    Base.metadata.create_all(
        _engine,
        tables=[
            ParentStudent.__table__,
            ParentGradeAlert.__table__,
            Semester.__table__,
            SemesterSubjectAverage.__table__,
            SemesterGradeReport.__table__
        ]
    )
    existing_tables = set(inspect(_engine).get_table_names())
    if 'assessment' in existing_tables:
        assessment_columns = {
            column['name'] for column in inspect(_engine).get_columns('assessment')
        }
        if 'semester_id' not in assessment_columns:
            with _engine.begin() as connection:
                connection.exec_driver_sql(
                    'ALTER TABLE assessment ADD COLUMN semester_id VARCHAR REFERENCES semester (id)'
                )

    if 'parent_grade_alert' in existing_tables:
        alert_columns = {
            column['name'] for column in inspect(_engine).get_columns('parent_grade_alert')
        }
        if 'semester_id' not in alert_columns:
            with _engine.begin() as connection:
                connection.exec_driver_sql(
                    'ALTER TABLE parent_grade_alert ADD COLUMN semester_id VARCHAR REFERENCES semester (id)'
                )
        if 'assessment_name' not in alert_columns:
            with _engine.begin() as connection:
                connection.exec_driver_sql(
                    'ALTER TABLE parent_grade_alert ADD COLUMN assessment_name VARCHAR'
                )

    if 'parent' in existing_tables:
        parent_columns = {
            column['name'] for column in inspect(_engine).get_columns('parent')
        }
        if 'password' not in parent_columns:
            with _engine.begin() as connection:
                connection.exec_driver_sql(
                    'ALTER TABLE parent ADD COLUMN password VARCHAR(20)'
                )
        with _engine.begin() as connection:
            connection.exec_driver_sql(
                'INSERT INTO parent_student (parent_id, student_id) '
                'SELECT parent.id, parent.student_id FROM parent '
                'WHERE parent.student_id IS NOT NULL AND NOT EXISTS ('
                'SELECT 1 FROM parent_student '
                'WHERE parent_student.parent_id = parent.id '
                'AND parent_student.student_id = parent.student_id)'
            )

    if 'rank' in existing_tables:
        rank_columns = {
            column['name'] for column in inspect(_engine).get_columns('rank')
        }
        if 'semester_id' not in rank_columns:
            with _engine.begin() as connection:
                connection.exec_driver_sql(
                    'ALTER TABLE rank ADD COLUMN semester_id VARCHAR REFERENCES semester (id)'
                )
                connection.exec_driver_sql(
                    'CREATE INDEX IF NOT EXISTS ix_rank_semester_id ON rank (semester_id)'
                )


def create_admin_account(_engine):
    # Create a session factory and a new session
    _session = sessionmaker(bind=_engine)
    session = _session()
    exist = session.query(Admin).filter(
        Admin.fullname == var.ADMIN_USER_NAME
    ).first()
    # cahking if the user already exsit
    if not exist:
        # Try to add the admin user, commit if successful, rollback on error
        try:
            admin = Admin(ID=var.ID(), fullname=var.ADMIN_USER_NAME, password=var.ADMIN_PASSWORD)
            session.add(admin)
            session.commit()
            print("Admin user added successfully.")
        except Exception as e:
            session.rollback()  # Rollback the transaction in case of error
            print(f"Error occurred while adding admin: {e}")
        finally:
            session.close()  # Always close the session to clean up resources
    else:
        print('user already exist.')


def default_subject(_engine):
    from utility.data_processor import read_from_json

    _session = sessionmaker(bind=_engine)
    session = _session()
    default_subjects = read_from_json()[1]['Permanent']['subjects']
    for key in default_subjects:
        try:
            subject = Subjects(var.ID(),key,var.SUBJECT_PRIVLAGE[0])
            session.add(subject)
            session.commit()
        except Exception as e:
            session.rollback()
            return e
    return 'Subjects was Added Successfully'