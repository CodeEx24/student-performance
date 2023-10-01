from models import StudentClassGrade, Class, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, Course, ClassGrade, ClassSubjectGrade, db
from sqlalchemy import desc, distinct, func
import re
from werkzeug.security import check_password_hash, generate_password_hash
import datetime


from static.js.utils import convertGradeToPercentage, checkStatus


def getAllClassAverageWithPreviousYear(str_teacher_id):
    try:
        # This could be dynamic depending on the needs/whats the best
        current_year = datetime.datetime.now().year

        data_class_grade_handle = (
            db.session.query(
                ClassSubject,
                Class,
                ClassGrade,
                Course,
            )
            .join(Class, ClassSubject.ClassId == Class.ClassId)
            .join(ClassGrade, Class.ClassId == ClassGrade.ClassId)
            .join(Course, Class.CourseId == Course.CourseId)
            .filter(ClassSubject.TeacherId == str_teacher_id, Class.Batch == current_year-1)
            .distinct(Class.CourseId, Class.Year, Class.Batch)
            .order_by(desc(Class.Year))
            # I Limit this into 8 because teacher cannot have many classes and the data sets made are distributed almost all of them
            .limit(5)
            # Once the data sets is fixed this can replace the previous line
            # .all()
        )

        if data_class_grade_handle:
            list_data_class_grade = []

            for class_grade_handle in data_class_grade_handle:
                # Calculate class name
                class_name = f"{class_grade_handle.Course.CourseCode} {class_grade_handle.Class.Year}-{class_grade_handle.Class.Section} ({class_grade_handle.Class.Batch})"

                num_class_batch = class_grade_handle.Class.Batch
                num_class_section = class_grade_handle.Class.Section

                dict_class_grade_handle = {
                    'Class': class_name,
                    'AYear': class_grade_handle.Class.Year,
                    'BSection': num_class_section,
                    'Batch': num_class_batch,
                    'ListGrade': []
                }

                list_grade = []
                # 2022 - 4-i = 3 = 2019 1st Year
                #       4-2 = 2 = 2020 2nd Year
                # 4th year 2022 -
                # 3rd year 2021
                # 2nd year 2020
                # 1st year 2019
                for i in range(1, class_grade_handle.Class.Year+1):

                    batch = class_grade_handle.Class.Batch - class_grade_handle.Class.Year + i

                    class_grade_result = (
                        db.session.query(
                            Class,
                            ClassGrade,
                        )
                        .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                        .filter(Class.Year == i, Class.Batch == batch, Class.Section == num_class_section)
                        # I Limit this into 8 because teacher cannot have many classes and the data sets made are distributed almost all of them
                        .first()
                        # Once the data sets is fixed this can replace the previous line
                        # .all()
                    )

                    list_grade.append(
                        {'x': class_grade_result.Class.Batch, 'y': convertGradeToPercentage(class_grade_result.ClassGrade.Grade)})

                dict_class_grade_handle['ListGrade'].extend(list_grade)

                list_data_class_grade.append(dict_class_grade_handle)

            # Return the list of class grades and the lowest/highest grades dictionary
            return (list_data_class_grade)
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getHighLowAverageClass(str_teacher_id):

    try:
        current_year = datetime.datetime.now().year

        data_lowest_grade_class_handle = (
            db.session.query(
                ClassSubject,
                Class,
                ClassGrade,
                Course,
            )
            .join(Class, ClassSubject.ClassId == Class.ClassId)
            .join(ClassGrade, Class.ClassId == ClassGrade.ClassId)
            .join(Course, Class.CourseId == Course.CourseId)
            .filter(ClassSubject.TeacherId == str_teacher_id, Class.Batch == current_year-1)
            .order_by(ClassGrade.Grade.desc())
            .first()
        )

        data_highest_grade_class_handle = (
            db.session.query(
                ClassSubject,
                Class,
                ClassGrade,
                Course,
            )
            .join(Class, ClassSubject.ClassId == Class.ClassId)
            .join(ClassGrade, Class.ClassId == ClassGrade.ClassId)
            .join(Course, Class.CourseId == Course.CourseId)
            .filter(ClassSubject.TeacherId == str_teacher_id, Class.Batch == current_year-1)
            .order_by(ClassGrade.Grade)
            .first()
        )

        highest_grade = round(data_highest_grade_class_handle.ClassGrade.Grade, 2)
        lowest_grade = round(data_lowest_grade_class_handle.ClassGrade.Grade, 2)

        highest_class = f"{data_highest_grade_class_handle.Course.CourseCode} {data_highest_grade_class_handle.Class.Year}-{data_highest_grade_class_handle.Class.Section} ({data_highest_grade_class_handle.Class.Batch})"
        lowest_class = f"{data_lowest_grade_class_handle.Course.CourseCode} {data_lowest_grade_class_handle.Class.Year}-{data_lowest_grade_class_handle.Class.Section} ({data_lowest_grade_class_handle.Class.Batch})"

        # Return the list of class grades and the lowest/highest grades dictionary
        return {
            "highest": highest_grade,
            "highestClass": highest_class,
            "lowest": lowest_grade,
            "lowestClass": lowest_class
        }

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getSubjectCount(str_teacher_id):
    try:
        data_subject_amount = (
            db.session.query(
                func.count(distinct(ClassSubject.SubjectId))
            )
            .filter(ClassSubject.TeacherId == str_teacher_id)
            .scalar()
        )

        return {"subjectCount": data_subject_amount}
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getPassFailRates(str_teacher_id):
    try:

        data_pass_fail_rates = (
            db.session.query(
                ClassSubject,
                ClassSubjectGrade,
                Class,
                Subject
            )
            .join(ClassSubjectGrade, ClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
            .filter(ClassSubject.TeacherId == str_teacher_id)
            .distinct(Class.CourseId, Class.Year, Class.Batch)
            .order_by(desc(Class.Batch))
            .all()
        )

        if data_pass_fail_rates:
            list_pass_fail_rates = []

            for pass_fail_rates in data_pass_fail_rates:
                dict_pass_fail_rate = {
                    'Year': pass_fail_rates.Class.Batch,
                    'Passed': pass_fail_rates.ClassSubjectGrade.Passed,
                    'Failed': pass_fail_rates.ClassSubjectGrade.Failed,
                    'Dropout': pass_fail_rates.ClassSubjectGrade.Dropout,
                }
                list_pass_fail_rates.append(dict_pass_fail_rate)

            aggregated_data = {}

            for entry in list_pass_fail_rates:
                year = entry['Year']
                passed = entry['Passed']
                failed = entry['Failed']
                dropout = entry['Dropout']

                if year in aggregated_data:
                    aggregated_data[year]['Passed'] += passed
                    aggregated_data[year]['Failed'] += failed
                    aggregated_data[year]['Dropout'] += dropout
                else:
                    aggregated_data[year] = {
                        'Year': year,
                        'Passed': passed,
                        'Failed': failed,
                        'Dropout': dropout
                    }

            return list(aggregated_data.values())

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getTopPerformerStudent(str_teacher_id, count):
    try:

        data_top_performer_student = (
            db.session.query(
                ClassSubject,
                StudentClassSubjectGrade,
                StudentClassGrade,
                Student,
                Course,
                Class,
            )
            .join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(StudentClassGrade, StudentClassSubjectGrade.StudentId == StudentClassGrade.StudentId)
            .join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId)
            .join(Course, Course.CourseId == Class.CourseId)
            .filter(ClassSubject.TeacherId == str_teacher_id)
            .order_by(desc(Class.Batch), (StudentClassGrade.Grade))
            .all()
        )

        if data_top_performer_student:
            list_data_top_performer_student = []
            seen_student_numbers = set()  # To keep track of seen student numbers
            added_count = 0  # To count the number of added objects

            for top_performer_student in data_top_performer_student:
                student_number = top_performer_student.Student.StudentNumber

                # Check if we have already seen this student number
                if student_number not in seen_student_numbers:
                    class_name = f"{top_performer_student.Course.CourseCode} {top_performer_student.Class.Year}-{top_performer_student.Class.Section}"

                    dict_pass_fail_rate = {
                        'StudentNumber': student_number,
                        'StudentName': top_performer_student.Student.Name,
                        'Grade': top_performer_student.StudentClassGrade.Grade,
                        'Batch': top_performer_student.Class.Batch,
                        'Class': class_name,
                        'TeacherNum': top_performer_student.ClassSubject.TeacherId
                    }

                    list_data_top_performer_student.append(dict_pass_fail_rate)

                    # Add the student number to the set of seen numbers
                    seen_student_numbers.add(student_number)

                    added_count += 1  # Increment the added count

                    # Check if we have added the desired number of objects
                    if added_count >= count:
                        break  # Exit the loop if count is reached

            return list_data_top_performer_student

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getStudentClassSubjectGrade(str_teacher_id):
    try:
        current_year = datetime.datetime.now().year

        # Subject , Grade,
        # Class - Semester, Batch, Class Code

        data_class_subject_grade_handle = (
            db.session.query(
                ClassSubject,
                StudentClassSubjectGrade,
                Subject,
                Class,
                Course,
                Student
            )
            .join(StudentClassSubjectGrade, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Subject, Subject.SubjectId == ClassSubject.SubjectId)
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(Course, Course.CourseId == Class.CourseId)
            .join(Student, Student.StudentId == StudentClassSubjectGrade.StudentId)
            .filter(ClassSubject.TeacherId == str_teacher_id, Class.Batch >= current_year-4)
            .order_by(desc(Course.CourseCode), desc(Class.Batch), desc(Class.Year), desc(Class.Semester))
            .all()
        )

        if data_class_subject_grade_handle:
            list_data_class_subject_grade = []
            unique_classes = set()

            for class_subject_grade in data_class_subject_grade_handle:
                # Get the class name
                class_name = f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Class.Year}-{class_subject_grade.Class.Section}"

                dict_class_subject_grade = {
                    'StudentId': class_subject_grade.Student.StudentId,
                    'StudentNumber': class_subject_grade.Student.StudentNumber,
                    'StudentName': class_subject_grade.Student.Name,
                    'Class': class_name,
                    'Batch': class_subject_grade.Class.Batch,
                    'Semester': class_subject_grade.Class.Semester,
                    'Grade': class_subject_grade.StudentClassSubjectGrade.Grade,
                    'SubjectCode': class_subject_grade.Subject.SubjectCode
                }

                list_data_class_subject_grade.append(dict_class_subject_grade)
                unique_classes.add(class_name)

            sorted_unique_classes = sorted(unique_classes)

            # Return the list of class grades and the lowest/highest grades dictionary
            return {'ClassSubjectGrade': list_data_class_subject_grade, 'Classes': list(sorted_unique_classes)}
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None

# RENDER THIS IN FRONTEND


def getAllClass(str_teacher_id):
    try:
        current_year = datetime.datetime.now().year

        data_class_subject_grade_handle = (
            db.session.query(
                ClassSubject,
                Class, Course
            )
            .join(Class, Class.ClassId == ClassSubject.ClassId)
            .join(Course, Course.CourseId == Class.CourseId)
            .filter(ClassSubject.TeacherId == str_teacher_id, Class.Batch == current_year - 1)
            .order_by(desc(Class.CourseId), Class.Year, Class.Section)
            .all()
        )

        if data_class_subject_grade_handle:
            list_classes = []
            seen_class_name = set()  # Initialize a set to track seen ClassIds

            for class_subject_grade in data_class_subject_grade_handle:
                class_name = f"{class_subject_grade.Course.CourseCode} {class_subject_grade.Class.Year}-{class_subject_grade.Class.Section}"

                # Check if the ClassId is not in the seen_class_name set
                if class_name not in seen_class_name:
                    # Get the class name
                    class_obj = {
                        'ClassId': class_subject_grade.Class.ClassId,
                        'ClassName': class_name
                    }

                    # Add class_name to the seen_class_name set
                    seen_class_name.add(class_name)

                    # Add class_obj to the list_classes
                    list_classes.append(class_obj)

            # Return the list of class objects
            return {'Classes': list_classes}
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getClassPerformance(class_id):
    try:
        class_grade = (
            db.session.query(
                ClassGrade, Class, Course
            )
            .join(Class, Class.ClassId == ClassGrade.ClassId)
            .join(Course, Course.CourseId == Class.CourseId)
            .filter(ClassGrade.ClassId == class_id)
            .first()
        )
        if class_grade:
            class_name = f"{class_grade.Course.CourseCode} {class_grade.Class.Year}-{class_grade.Class.Section} ({class_grade.Class.Batch})"
            
            num_class_batch = class_grade.Class.Batch
            num_class_section = class_grade.Class.Section

            dict_class_grade = {
                'Class': class_name,
                'Batch': num_class_batch,
                'ListGrade': [],
                'PresidentLister': class_grade.ClassGrade.PresidentsLister,
                'DeanLister': class_grade.ClassGrade.DeansLister
            }
            
            list_grade = []
            for i in range(1, class_grade.Class.Year+1):

                batch = class_grade.Class.Batch - class_grade.Class.Year + i

                class_grade_result = (
                    db.session.query(
                        Class,
                        ClassGrade,
                    )
                    .join(ClassGrade, ClassGrade.ClassId == Class.ClassId)
                    .filter(Class.Year == i, Class.Batch == batch, Class.Section == num_class_section)
                    .first()

                )

                list_grade.append(
                    {'x': class_grade_result.Class.Batch, 'y': convertGradeToPercentage(class_grade_result.ClassGrade.Grade)})

            dict_class_grade['ListGrade'].extend(list_grade)
            return (dict_class_grade)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getStudentPerformance(str_student_id):
    try:
        list_student_performance = (
            db.session.query(StudentClassGrade, Class)
            .join(Class, StudentClassGrade.ClassId == Class.ClassId)
            .filter(StudentClassGrade.StudentId == str_student_id)
            .order_by(desc(Class.Batch), desc(Class.Semester))
            .all()
        )

        if list_student_performance:
            list_performance_data = []  # Initialize a list to store dictionary data
            for gpa in list_student_performance:

                gpa_dict = {
                    'Grade': convertGradeToPercentage(gpa.StudentClassGrade.Grade),
                    'Semester': gpa.Class.Semester,
                    'Year': gpa.Class.Batch,
                }
                # Append the dictionary to the list
                list_performance_data.append(gpa_dict)

            # Check for missing entries
            batch_semester_map = {(gpa_dict["Year"], semester): False for semester in range(
                1, 4) for gpa_dict in list_performance_data}

            for gpa_dict in list_performance_data:
                batch_semester_map[(gpa_dict["Year"],
                                    gpa_dict["Semester"])] = True

            missing_entries = []
            for (batch, semester), is_present in batch_semester_map.items():
                if not is_present:
                    missing_entries.append({
                        "Year": batch,
                        "Grade": 0,
                        "Semester": semester
                    })

            # Append missing entries to list_performance_data
            list_performance_data.extend(missing_entries)

            # Sort the combined list based on year descending and semester descending
            sorted_list_performance_data = sorted(list_performance_data, key=lambda x: (
                x['Year'], x['Semester']), reverse=True)

            return sorted_list_performance_data
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getFacultyData(str_teacher_id):
    try:
        data_faculty = (
            db.session.query(Faculty).filter(
                Faculty.TeacherId == str_teacher_id).first()
        )

        if data_faculty:
            dict_faculty_data = {
                "TeacherId": data_faculty.TeacherId,
                "TeacherNumber": data_faculty.TeacherNumber,
                "Name": data_faculty.Name,
                "ResidentialAddress": data_faculty.ResidentialAddress,
                "Email": data_faculty.Email,
                "MobileNumber": data_faculty.MobileNumber,
                "Gender": "Male" if data_faculty.Gender == 1 else "Female",
            }

            return (dict_faculty_data)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def updateFacultyData(str_teacher_id, email, number, residential_address):
    try:
        if not re.match(r'^[\w\.-]+@[\w\.-]+$', email):
            return {"type": "email", "status": 400}

        if not re.match(r'^09\d{9}$', number):
            return {"type": "mobile", "status": 400}

        if residential_address is None or residential_address.strip() == "":
            return {"type": "residential", "status": 400}
        
        # Update the student data in the database
        data_faculty = db.session.query(Faculty).filter(
            Faculty.TeacherId == str_teacher_id).first()
        
        if data_faculty:
            data_faculty.Email = email
            data_faculty.MobileNumber = number
            data_faculty.ResidentialAddress = residential_address
            db.session.commit()

            return {"message": "Data updated successfully", "email": email, "number": number, "residential_address": residential_address, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}


def updatePassword(str_teacher_id, password, new_password, confirm_password):
    try:
        data_faculty = db.session.query(Faculty).filter(
            Faculty.TeacherId == str_teacher_id).first()

        if data_faculty:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_faculty.Password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(
                    new_password)
                data_faculty.Password = new_hashed_password
                db.session.commit()
                return {"message": "Password changed successfully", "status": 200}

            else:
                return {"message": "Changing Password was unsuccessful. Please try again.", "status": 400}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}


# def getAllClassAverage(str_teacher_id):
#     try:
#         current_year = datetime.datetime.now().year

#         data_class_grade_handle = (
#             db.session.query(
#                 ClassSubject,
#                 Class,
#                 ClassGrade,
#                 Course,
#             )
#             .join(Class, ClassSubject.ClassId == Class.ClassId)
#             .join(ClassGrade, Class.ClassId == ClassGrade.ClassId)
#             .join(Course, Class.CourseId == Course.CourseId)
#             .filter(ClassSubject.TeacherId == str_teacher_id, Class.Batch == current_year-1)
#             .distinct(Class.CourseId, Class.Year, Class.Batch)
#             # I Limit this into 8 because teacher cannot have many classes and the data sets made are distributed almost all of them
#             .limit(6)
#             # Once the data sets is fixed this can replace the previous line
#             # .all()
#         )

#         if data_class_grade_handle:
#             list_data_class_grade = []

#             for class_grade_handle in data_class_grade_handle:
#                 # Calculate class name
#                 class_name = f"{class_grade_handle.Course.CourseId} {class_grade_handle.Class.Year}-{class_grade_handle.Class.Section} ({class_grade_handle.Class.Batch})"

#                 dict_class_grade_handle = {
#                     'Class': class_name,
#                     'Year': class_grade_handle.Class.Year,
#                     'Section': class_grade_handle.Class.Section,
#                     'Batch': class_grade_handle.Class.Batch,
#                     'Grade': class_grade_handle.ClassGrade.Grade
#                 }

#                 list_data_class_grade.append(dict_class_grade_handle)

#             # Return the list of class grades and the lowest/highest grades dictionary
#             return (list_data_class_grade)
#         else:
#             return None

#     except Exception as e:
#         # Handle the exception here, e.g., log it or return an error response
#         return None
