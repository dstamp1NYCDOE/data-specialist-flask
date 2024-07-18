from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField, URLField
from wtforms.validators import DataRequired, Regexp, InputRequired

from werkzeug.utils import secure_filename

import datetime as dt

COHORT_YEAR_CHOICES = [
    ("4", "Cohort 2024/Class of 2028"),
    ("3", "Cohort 2023/Class of 2027"),
    ("2", "Cohort 2022/Class of 2026"),
    ("1", "Cohort 2021/Class of 2025"),
    ("Z", "Cohort 2020/Class of 2024"),
]


school_year_and_semester_choices = [
    ("2024-7", "Summer 2025"),
    ("2024-2", "Spring 2025"),
    ("2024-1", "Fall 2024"),
    ("2023-7", "Summer 2024"),
    ("2023-2", "Spring 2024"),
    ("2023-1", "Fall 2023"),
    ("2022-7", "Summer 2023"),
    ("2022-2", "Spring 2023"),
    ("2022-1", "Fall 2022"),
    ("2021-7", "Summer 2022"),
    ("2021-2", "Spring 2022"),
    ("2021-1", "Fall 2021"),
]


MARKING_PERIOD_CHOICES = [
    ("S1-MP1", "Fall MP1"),
    ("S1-MP2", "Fall MP2"),
    ("S1-MP3", "Fall MP3"),
    ("S2-MP1", "Spring MP1"),
    ("S2-MP2", "Spring MP2"),
    ("S2-MP3", "Spring MP3"),
]

SEMESTER_CHOICES = [
    ("S1-MP1", "Fall MP1"),
    ("S1-MP2", "Fall MP2"),
    ("S1-MP3", "Fall MP3"),
    ("S2-MP1", "Spring MP1"),
    ("S2-MP2", "Spring MP2"),
    ("S2-MP3", "Spring MP3"),
]

reports_choices = [
    ("scripts.programming.class_lists", "Class Lists"),
    (
        "scripts.surveys.connect_google_survey_with_class_lists",
        "Class Lists with Google Sheets Data",
    ),
]


class SemesterSelectForm(FlaskForm):
    year_and_semester = SelectField(
        "School Year and Semester",
        choices=school_year_and_semester_choices,
    )

    def __init__(self, *args, **kwargs):
        super(ClassListWithGoogleFormResultsForm, self).__init__(*args, **kwargs)
        self.report.data = "scripts.programming.class_lists"


class GsheetForm(FlaskForm):
    gsheet_category = SelectField(
        "Google Sheet Category",
        choices=[
            ("master_schedule_planning", "Master Schedule Planning"),
            ("summer_school_gradebooks_hub", "Summer School Gradebooks Hub"),
            ("summer_school_attendance_hub", "Summer School Attendance Hub"),
        ],
    )
    gsheet_url = URLField(
        "Google Sheet URL",
        description="Share the Google Sheet with hsfi-data-dashboard@quickstart-1567988320342.iam.gserviceaccount.com",
    )
    year_and_semester = SelectField(
        "School Year and Semester",
        choices=school_year_and_semester_choices,
    )


def set_default_year_and_semester():
    school_year = session["school_year"]
    term = session["term"]
    year_and_semester = f"{school_year}-{term}"
    return year_and_semester


class FileForm(FlaskForm):
    file = FileField(validators=[FileRequired()])
    download_date = DateField(default=dt.datetime.today)
    year_and_semester = SelectField(
        "School Year and Semester",
        choices=school_year_and_semester_choices,
        default=set_default_year_and_semester,
    )


class JupiterUpdateForm(FlaskForm):
    year_and_semester = SelectField(
        "School Year and Semester",
        choices=school_year_and_semester_choices,
    )
    report = SelectField(
        "Jupiter File",
        choices=[
            ("assignments", "Student Assignments"),
            ("jupiter-master-schedule", "Master Schedule"),
            ("rosters-and-grades", "Grades and Rosters"),
            ("jupiter-period-attendance", "Period Attendance"),
        ],
    )


class ReportForm(FlaskForm):
    year_and_semester = SelectField(
        "School Year and Semester",
        choices=school_year_and_semester_choices,
    )
    report = SelectField("Report", choices=reports_choices)


class ClassListsForm(ReportForm):
    def __init__(self, *args, **kwargs):
        super(ClassListWithGoogleFormResultsForm, self).__init__(*args, **kwargs)
        self.report.data = "scripts.programming.class_lists"


class ClassListWithGoogleFormResultsForm(ReportForm):
    def __init__(self, *args, **kwargs):
        super(ClassListWithGoogleFormResultsForm, self).__init__(*args, **kwargs)
        self.report.data = "scripts.surveys.connect_google_survey_with_class_lists"

    gsheet_url = StringField(
        "Google Sheet",
        validators=[
            DataRequired("URL is required"),
        ],
    )

    student_id_columns = SelectField(
        "Which Column in the Google Sheet does 'StudentID' Appear?",
        choices=[
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
            ("E", "E"),
        ],
    )


class SelectStudentForm(FlaskForm):

    StudentID = SelectField(
        "Select Student",
        choices=[(0, "Select Student")],
        validators=[InputRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
