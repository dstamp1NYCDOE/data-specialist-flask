from flask import Blueprint

import app.scripts.utils as utils

scripts = Blueprint("scripts", __name__, template_folder="")
files_df = utils.return_dataframe_of_files()
photos_df = utils.return_dataframe_of_photos()
gsheets_df = utils.return_dataframe_of_gsheets()


from app.scripts.assignments import routes

from app.scripts.attendance import attendance
from app.scripts.attendance.rdal_analysis import routes
from app.scripts.attendance.confirmation_sheets import routes
from app.scripts.attendance.jupiter import routes
from app.scripts.attendance.late_analysis import routes
from app.scripts.attendance.cut_analysis import routes
from app.scripts.attendance.historical_period_attd import routes
from app.scripts.attendance.CAASS import routes

from app.scripts.college_and_career import routes

from app.scripts.family_engagement import routes
from app.scripts.family_engagement.weekly_assignment import routes

from app.scripts.dataspecialist import routes
from app.scripts.dataspecialist.sy2425 import routes

from app.scripts.officialclass import routes
from app.scripts.commutes import commutes
from app.scripts.classwork import routes

from app.scripts.organization import routes
from app.scripts.organization.gsheet_classlist import routes
from app.scripts.organization.locker_assignment_letters import routes
from app.scripts.organization.metrocards import routes
from app.scripts.organization.mailinglabels import routes
from app.scripts.organization.ms_teams import routes
from app.scripts.organization.gather_teacher_input_per_student_spreadsheet import routes

from app.scripts.pbis import routes
from app.scripts.pbis.smartpass import routes
from app.scripts.pbis.screener import routes
from app.scripts.pbis.phone_call_tracker import routes
from app.scripts.pbis.student_network import routes


from app.scripts.privileges import routes
from app.scripts.programming import routes
from app.scripts.programming.spring_scheduling import routes
from app.scripts.programming.ICT_sections import routes
from app.scripts.programming.jupiter import routes
from app.scripts.progress_towards_graduation import routes
from app.scripts.scholarship import routes
from app.scripts.scholarship.reportcards import routes
from app.scripts.scholarship.egg import routes
from app.scripts.scholarship.stars import routes

from app.scripts.summer import routes
from app.scripts.summer.attendance import routes
from app.scripts.summer.organization import routes
from app.scripts.summer.programming import routes
from app.scripts.summer.testing import routes
from app.scripts.summer.testing.regents_organization import routes
from app.scripts.testing import routes
