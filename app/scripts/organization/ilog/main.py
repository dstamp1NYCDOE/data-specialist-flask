import pyautogui
import time
import pandas as pd


def main(form, request):    # Extract form data
    
    date_str = form.intervention_date.data.strftime("%m%d%y")
    source_str = form.source_str.data
    action_taken_str = form.action_taken_str.data
    comment_str = form.comments_str.data
    ats_region = form.ats_region.data

    student_lst_str = form.students_str.data
    student_lst = []
    if student_lst_str != '':
        student_lst = student_lst_str.split("\r\n")
        student_lst = [int(x) for x in student_lst]

    # waits 5 seconds to allow user to switch to the ATS screen
    time.sleep(5)
    for student_id in student_lst:
        if ats_region == "ATSSUM":
            ilog_atssum(student_id, date_str, source_str, action_taken_str, comment_str)

    return "iLog automation completed successfully."


def ilog_atssum(StudentID, date_str, source_str, action_taken_str,comment_str):
    time.sleep(0.1)
    # type StudentID number
    pyautogui.write(str(StudentID))
    # type enter key
    pyautogui.press("enter")
    ## check if the student has ever had an iLog before
    try:
        pyautogui.locateOnScreen("app/scripts/summer/attendance/iLogUpdateScreenshot.png")
        # type f2 to add new iLog
        pyautogui.press("f5")
        has_ilog_flag = True
    except pyautogui.ImageNotFoundException:
        has_ilog_flag = False    

    # type date at 6 digit number
    pyautogui.write(date_str)
    pyautogui.keyUp('fn')
    # type source
    pyautogui.write(source_str)
    # type action taken
    pyautogui.write(action_taken_str)
    # type comment str
    pyautogui.keyUp('fn')
    pyautogui.write(comment_str)
    # type f2 to submit
    pyautogui.press("f2")
    # type f3 to go back to the student search if the current student has an iLog
    # otherwise, it will go back to the student search automatically
    if has_ilog_flag:
        pyautogui.press("f3")