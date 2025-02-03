

from flask import render_template, request, send_file, session


from app.scripts import scripts

from app.scripts.family_engagement.weekly_assignment.forms import AttendanceWeekOfForm

from app.scripts.family_engagement.weekly_assignment.main import return_weekly_assignments

@scripts.route("/family_engagement/weekly_assignment", methods=['GET','POST'])
def return_family_engagement_weekly_assignment():
    if request.method == 'GET':
        form = AttendanceWeekOfForm()
        return render_template('family_engagement/weekly_assignment/templates/form.html', form=form)
    else:
        form = AttendanceWeekOfForm(request.form)

        f, download_name = return_weekly_assignments(form, request)
        
        mimetype = "application/pdf"

        return send_file(
            f,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype,
        )