from flask import session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Regexp, InputRequired

from werkzeug.utils import secure_filename


class JupiterAttdUpload(FlaskForm):
    jupiter_attd_file = FileField(
        "Upload one day of Jupiter Attendance Export",
        validators=[FileRequired()],
    )

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
import datetime as dt

class MostImprovedAttendanceForm(FlaskForm):
    """Form for selecting the award month for Most Improved Attendance analysis"""
    
    award_month = SelectField(
        'Award Month',
        validators=[DataRequired()],
        choices=[],
        description='Select the month for which to generate Most Improved Attendance awards'
    )
    
    submit = SubmitField('Generate Awards')
    
    def __init__(self, *args, **kwargs):
        super(MostImprovedAttendanceForm, self).__init__(*args, **kwargs)
        
        # Generate month choices from September to current month
        current_date = dt.datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        # Determine school year start
        if current_month >= 9:  # Sept or later = current year
            school_year_start = current_year
        else:  # Before Sept = started last year
            school_year_start = current_year - 1
        
        # Build list of months from September onwards
        months = []
        start_month = 9  # September
        
        # Add months from Sept through Dec of school year start
        for month in range(start_month, 13):
            date_obj = dt.date(school_year_start, month, 1)
            months.append((
                date_obj.strftime('%Y-%m'),
                date_obj.strftime('%B %Y')
            ))
        
        # Add months from Jan through current month of next year
        if current_month < 9:  # We're in the spring semester
            for month in range(1, current_month + 1):
                date_obj = dt.date(school_year_start + 1, month, 1)
                months.append((
                    date_obj.strftime('%Y-%m'),
                    date_obj.strftime('%B %Y')
                ))
        
        self.award_month.choices = months    
