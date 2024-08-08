import pandas as pd
import numpy as np

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import Paragraph, PageBreak, Spacer, Image, Table, TableStyle, ListFlowable
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter, landscape

styles = getSampleStyleSheet()

import proctoring_todos

def return_checklist(data):
    print(data)
    exam_title = data.get('Exam',"")
    flowables = []
    
    paragraph = Paragraph(f"{exam_title} Regents Proctoring Checklist", styles["Heading1"])
    flowables.append(paragraph)

    paragraph = Paragraph(f"Directions: Complete this checklist as you administer the Regents exam. Initial next to each step. Exam specific information is on the back of the checklist. Additional pages guide you through the three phases of the administration. If you have any questions, call the Testing Office at x2021 or x2022", styles["Normal"])
    flowables.append(paragraph)


    paragraph = Paragraph(f"Pre-Exam", styles["Heading2"])
    flowables.append(paragraph)
    flowables.append(proctoring_todos.pre_exam_todos)

    paragraph = Paragraph(f"Starting Exam", styles["Heading2"])
    flowables.append(paragraph)
    pre_exam_todos = proctoring_todos.pre_exam_todos
    flowables.append(pre_exam_todos)


    paragraph = Paragraph(f"During Exam", styles["Heading2"])
    flowables.append(paragraph)
    during_exam_todos = proctoring_todos.during_exam_todos
    
    flowables.append(during_exam_todos)

    paragraph = Paragraph(f"Post-Exam", styles["Heading2"])
    flowables.append(paragraph)
    post_exam_todos = proctoring_todos.post_exam_todos
    flowables.append(post_exam_todos)

    paragraph = Paragraph(f"Proctor Signatures", styles["Heading2"])
    flowables.append(paragraph)
    paragraph = Paragraph(f"Directions: All proctors will sign and date to attest they followed NYSED and HSFI specific procedures while completing this proctoring assignment.", styles["Normal"])
    flowables.append(paragraph)
    flowables.append(proctoring_todos.signature_grid_table)

    return flowables
   
if __name__ == "__main__":
    data = {
    }
    return_checklist(data)
