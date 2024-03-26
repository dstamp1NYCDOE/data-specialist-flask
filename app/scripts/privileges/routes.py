import datetime as dt
from io import BytesIO

from flask import render_template, request, send_file, session, url_for, redirect


from app.scripts import scripts, files_df
import app.scripts.utils as utils

from app.main.forms import SelectStudentForm

@scripts.route("/privileges")
def return_privileges_reports():

    PrivilegesStudentLookupForm = SelectStudentForm()

    form_cards = [
        {'Title':'Student Privileges Lookup','Description':"Search individual student HSFI privileges","form":PrivilegesStudentLookupForm, 'route':'scripts.return_student_privileges_report'}
    ]

    return render_template('/privileges/templates/privileges/index.html', form_cards=form_cards)

from app.scripts.privileges.out_to_lunch import summary_page
@scripts.route("/privileges/student", methods=['GET','POST'])
def return_student_privileges_report():
    if request.method == "GET":
        form = SelectStudentForm()
        return redirect(url_for('scripts.return_privileges_reports'))
    else:
        form = SelectStudentForm(request.form)
        f = summary_page.return_student_letter(form, request)
        download_name = (
            f"Student_Privileges_report_{dt.datetime.today().strftime('%Y-%m-%d')}.pdf"
        )
        mimetype = "application/pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype,
        )