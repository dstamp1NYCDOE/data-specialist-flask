import pyautogui
import time
import pandas as pd


def main(form, request):
    filename = request.files[form.rdal_file.name]
    class_date = form.class_date.data
    ilog_date = class_date.strftime("%m%d%y")
    rdal_df = pd.read_csv(filename, skiprows=3)
    students_lst = rdal_df["Student ID"].tolist()

    time.sleep(5)
    for StudentID in students_lst:
        ilog_student_absence(StudentID, ilog_date, "AP", "1", "Automated phone call because student was absent")


def ilog_student_absence(StudentID, date_str, source_str, action_taken_str,comment_str):
    time.sleep(0.1)
    # type StudentID number
    pyautogui.write(str(StudentID))
    time.sleep(0.1)
    # type enter key
    pyautogui.press("enter")
    time.sleep(0.1)
    ## check if the student has ever had an iLog before
    try:
        pyautogui.locateOnScreen("app/scripts/summer/attendance/iLogUpdateScreenshot.png")
        # type f2 to add new iLog
        pyautogui.press("f5")
        time.sleep(0.1)
        has_ilog_flag = True
    except pyautogui.ImageNotFoundException:
        time.sleep(0.1) 
        has_ilog_flag = False    

    # type date at 6 digit number
    pyautogui.write(date_str)
    time.sleep(0.1)
    # type source (AP)
    pyautogui.keyUp('fn')
    pyautogui.write(source_str)
        
    # type action taken (1)
    pyautogui.write(action_taken_str)
    time.sleep(0.1)
    # type comment str (automated phone call because student was absent)
    pyautogui.keyUp('fn')
    pyautogui.write(comment_str)
    # type f2 to submit
    pyautogui.press("f2")
    time.sleep(0.1)

    if has_ilog_flag:
        # type f2 to update
        pyautogui.press("f3")
        time.sleep(0.1)

if __name__ == "__main__":
    
    student_id_list = [234645224,
                        216274555,
                        229110283,
                        237684212,
                        234996445,
                        235974243,
                        233874403,
                        214918864,
                        236209250,
                        247427958,
                        204376818,
                        235329232,
                        234826303,
                        231166315,
                        224244814,
                        206490195,
                        241874445,
                        215783432,
                        234836732,
                        245707237,
                        229255732,
                        221510118,
                        235720513,
                        208986489,
                        208206961,
                        234309938,
                        100999618,
                        245074745,
                        234052660,
                        208979351,
                        233785237,
                        234288520,
                        236218459,
                        215890013,
                        220132500,
                        234248144,
                        231973371,
                        233186469,
                        237847272,
                        235287661,
                        203377809,
                        234635837,
                        235959996,
                        234204410,
                        237164181,
                        236690293]
    time.sleep(5)
    ilog_date = "071425"
    for StudentID in student_id_list:
        ilog_student_absence(StudentID, ilog_date, "AP", "1", "Automated Phone call to parent because student was absent")