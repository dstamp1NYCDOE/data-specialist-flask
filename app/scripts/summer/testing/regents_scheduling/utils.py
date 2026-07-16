def return_full_exam_title(ExamTitle):
    
    exam_title_dict = {
        "ELA": "ELA",
        "Global": "Global History",
        "USH": "US History",
        "Alg1": "Algebra I",
        "Geo": "Geometry",
        "Alg2": "Algebra II/Trigonometry",
        "LE": "Living Environment",
        "Bio": "Biology",
        "ES": "Earth Science",
        "ESS": "Earth and Space Science",
        "Chem": "Chemistry",
        "Chem (old)": "Chemistry (old)",
        "Chem (new)": "Chemistry (new)",
        "Phys": "Physics",
    }
    return exam_title_dict.get(ExamTitle)