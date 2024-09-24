import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session, url_for, redirect


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.scripts.programming.jupiter.forms import JupiterMasterScheduleForm



import app.scripts.programming.ICT_sections.combine_ict_sections as combine_ict_sections
@scripts.route("/programming/stars/combine_ict", methods=['GET','POST'])
def return_combined_ict_for_stars():
    if request.method == 'GET':
        form = JupiterMasterScheduleForm(request.form)

        return combine_ict_sections.main(request, form)
    else:
        form = JupiterMasterScheduleForm(request.form)

        return combine_ict_sections.main(request, form)
