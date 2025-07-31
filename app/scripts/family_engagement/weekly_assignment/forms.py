from flask import session, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Regexp, InputRequired

from werkzeug.utils import secure_filename


from app.scripts import scripts, files_df
import app.scripts.utils.utils as utils
import pandas as pd

class AttendanceWeekOfForm(FlaskForm):
    week_of = SelectField(
        "Select Week Of",
        choices=[],
        validators=[InputRequired()],
    )

    def __init__(self, *args, **kwargs):
        super(AttendanceWeekOfForm, self).__init__(*args, **kwargs)

        school_year = session["school_year"]
        term = session["term"]
        year_and_semester = f"{school_year}-{term}"
        jupiter_attd_filename = utils.return_most_recent_report_by_semester(files_df, "jupiter_period_attendance", year_and_semester=year_and_semester)
        attendance_marks_df = utils.return_file_as_df(jupiter_attd_filename)

        dates_df = attendance_marks_df[['Date']].drop_duplicates()
        dates_df['date'] = pd.to_datetime(dates_df['Date'])
        dates_df['week_number'] = dates_df['date'].dt.isocalendar().week
        dates_df = dates_df.drop_duplicates(subset=['week_number'])
        
        dates_df['label'] = dates_df['Date'].apply(lambda x:f'Week of {x}')
        df = dates_df[['week_number','label']]
        self.week_of.choices = list(zip(*df.values.T))