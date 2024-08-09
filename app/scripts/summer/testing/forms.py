from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

from wtforms import DateField, SelectField
from wtforms.validators import DataRequired, Regexp, InputRequired


class CombinedRegentsRegistrationForm(FlaskForm):
    combined_regents_registration_spreadsheet = FileField(
        "Upload XLSX file of regents registrations",
        validators=[FileRequired()],
    )


class YABCRegentsRegistration(FlaskForm):
    combined_regents_registration_spreadsheet = FileField(
        "Upload XLSX file of regents registrations",
        validators=[FileRequired()],
    )
    yabc_1_08 = FileField(
        "Upload csv file of YABC 1.08",
        # validators=[FileRequired()],
    )


class RegentsOrderingForm(CombinedRegentsRegistrationForm):
    pass


class IdentifyExamOnlyForm(CombinedRegentsRegistrationForm):
    pass


class ProcessRegentsPreregistrationSpreadsheetForm(CombinedRegentsRegistrationForm):
    pass


class SummerRegentsSchedulingForm(CombinedRegentsRegistrationForm):
    pass


exam_title_choices = [
    ("ALL", "ALL"),
    ("ELA", "ELA"),
    ("Global", "Global History"),
    ("USH", "US History"),
    ("Alg1", "Algebra I"),
    ("Geo", "Geometry"),
    ("Alg2", "Algebra II/Trigonometry"),
    ("LE", "Living Environment"),
    ("ES", "Earth Science"),
    ("Chem", "Chemistry"),
    ("Phys", "Physics"),
]


class ReturnExamLabelsForm(FlaskForm):
    exam_title = SelectField(
        "Select Exam",
        choices=exam_title_choices,
        validators=[InputRequired()],
    )


class ReturnENLrostersForm(FlaskForm):
    exam_title = SelectField(
        "Select Exam",
        choices=exam_title_choices,
        validators=[InputRequired()],
    )
