from models import StudentClassGrade, Class, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, Course, Metadata, db
from sqlalchemy import desc
import re
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session

from static.js.utils import convertGradeToPercentage, checkStatus


def getCurrentUser():
    current_user_id = session.get('user_id')
    return Student.query.get(current_user_id)


def getStudentGpa(studentId):
    try:
        gpa = StudentClassGrade.query.filter_by(
            StudentId=studentId).join(Class, StudentClassGrade.ClassId == Class.ClassId).join(Metadata, Metadata.MetadataId == Class.MetadataId).order_by(desc(Metadata.Batch), desc(Metadata.Semester)).first()
        if gpa:
            dict_gpa = gpa.to_dict()
            return dict_gpa
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getStudentPerformance(str_student_id):
    try:
        list_student_performance = (
            db.session.query(StudentClassGrade, Class, Metadata)
            .join(Class, StudentClassGrade.ClassId == Class.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .filter(StudentClassGrade.StudentId == str_student_id)
            .order_by(desc(Metadata.Batch), desc(Metadata.Semester))
            .all()
        )

        if list_student_performance:
            list_performance_data = []  # Initialize a list to store dictionary data
            for gpa in list_student_performance:

                gpa_dict = {
                    'Grade': convertGradeToPercentage(gpa.StudentClassGrade.Grade),
                    'Semester': gpa.Metadata.Semester,
                    'Year': gpa.Metadata.Batch,
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

def getLatestSubjectGrade(str_student_id):
    try:
        data_latest_class_subject = (
            db.session.query(StudentClassSubjectGrade, ClassSubject, Class)
            .join(ClassSubject, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Class, ClassSubject.ClassId == Class.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .filter(StudentClassSubjectGrade.StudentId == str_student_id)
            .order_by(desc(Metadata.Batch), desc(Metadata.Semester))
            .first()
        )
        
        if data_latest_class_subject:

            data_class_subject_grade = (
                db.session.query(
                    ClassSubject, StudentClassSubjectGrade, Subject, Class, Metadata)
                .join(StudentClassSubjectGrade, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId)
                .join(Class, Class.ClassId == ClassSubject.ClassId)
                .join(Metadata, Metadata.MetadataId == Class.MetadataId)
                .join(Subject, ClassSubject.SubjectId == Subject.SubjectId)
                .filter(StudentClassSubjectGrade.StudentId == str_student_id, ClassSubject.ClassId == data_latest_class_subject.Class.ClassId, Metadata.Semester == data_latest_class_subject.Metadata.Semester)
                .all()
            )
            if data_class_subject_grade:
                list_class_subject_grade = []

                for class_subject_grade in data_class_subject_grade:
                    dict_class_subject_grade = {
                        'Code': class_subject_grade.Subject.SubjectCode,
                        'Units': format(class_subject_grade.Subject.Units, '.2f'),
                        'Grade': class_subject_grade.StudentClassSubjectGrade.Grade,
                    }
                    # Append the dictionary to the list
                    list_class_subject_grade.append(dict_class_subject_grade)
                if list_class_subject_grade:

                    return (list_class_subject_grade)
                else:
                    return None
            else:
                return None

    except Exception as e:

        # Handle the exception here, e.g., log it or return an error response
        return None

def getCoursePerformance(str_student_id):
    try:
        data_course_enrolled = (
            db.session.query(CourseEnrolled)
            .filter(CourseEnrolled.StudentId == str_student_id)
            .order_by(desc(CourseEnrolled.DateEnrolled))
            .first()
        )

        
        if data_course_enrolled:
            data_course_performance = (
                db.session.query(CourseGrade)
                .filter(CourseGrade.CourseId == data_course_enrolled.CourseId)
                .order_by(desc(CourseGrade.Year))
                .limit(10)
                # .all()
            )

            if data_course_performance:
                list_course_performance = []
                data_course = {
                    "Course": data_course_enrolled.CourseId, "List": []
                }

                for course_performance in data_course_performance:
                    dict_course_performance = {
                        'Grade': convertGradeToPercentage(course_performance.Grade),
                        'Year': course_performance.Year
                    }

                    list_course_performance.append(dict_course_performance)

                data_course["List"] = list_course_performance
                return data_course
            else:
                return None
        else:
            return None

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getOverallGrade(str_student_id):
    try:
        data_overall_class_grade = StudentClassGrade.query.filter_by(
            StudentId=str_student_id).all()

        if data_overall_class_grade:
            total_grade = 0
            grade_count = 0

            for overall_class_grade in data_overall_class_grade:

                total_grade += overall_class_grade.Grade
                grade_count += 1

            total_average_grade = total_grade / grade_count

            dict_total_average_grade = {"Grade": total_average_grade}

            return (dict_total_average_grade)

        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def getSubjectsGrade(str_student_id):
    try:
        data_student_class_subject_grade = (
            db.session.query(StudentClassSubjectGrade, ClassSubject, Class, Course, Subject, Metadata )
            .join(ClassSubject, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Class, ClassSubject.ClassId == Class.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(Course, Course.CourseId == Metadata.CourseId)
            .join(Subject, ClassSubject.SubjectId == Subject.SubjectId)
            .filter(StudentClassSubjectGrade.StudentId == str_student_id)
            .order_by(desc(Metadata.Batch), desc(Metadata.Semester))
            .all()
        )
        
        # print('data_student_class_subject_grade: '. )
        
        if data_student_class_subject_grade:
            class_combinations = set()
            dict_class_group = {}
            list_student_class_subject_grade = []

            for student_class_subject_grade in data_student_class_subject_grade:
                teacher_name = ""
                
                # Check if teacher exist
                if student_class_subject_grade.ClassSubject.TeacherId:
                    # Query the teacher
                    data_teacher = (
                        db.session.query(Faculty)
                        .filter(Faculty.TeacherId == student_class_subject_grade.ClassSubject.TeacherId)
                        .first()
                    )
                    teacher_name = data_teacher.Name
                
                
                class_combination = (
                    student_class_subject_grade.Class.ClassId,
                    student_class_subject_grade.Metadata.Batch,
                    student_class_subject_grade.Metadata.Semester
                )
                if class_combination not in class_combinations:
                    class_combinations.add(class_combination)

                    # Check if existing in the list table already the ClassId and semester so it wont reiterate the query
                    data_student_class_grade = (
                        db.session.query(StudentClassGrade)
                        .filter(StudentClassGrade.StudentId == str_student_id, StudentClassGrade.ClassId == student_class_subject_grade.Class.ClassId)
                        .first()
                    ) 
                    dict_class_group = {
                        "Batch": student_class_subject_grade.Metadata.Batch,
                        "GPA": format(data_student_class_grade.Grade, '.2f') if data_student_class_grade and data_student_class_grade.Grade is not None else "No GPA yet",
                        "Semester": student_class_subject_grade.Metadata.Semester,
                        "Subject": []
                    }

                    list_student_class_subject_grade.append(dict_class_group)
                
                # Append the subject details to the existing class group
                subject_details = {
                    "Grade": format(student_class_subject_grade.StudentClassSubjectGrade.Grade, '.2f') if student_class_subject_grade.StudentClassSubjectGrade.Grade is not None else "0.00",
                    "Subject": student_class_subject_grade.Subject.Name,
                    "Code": student_class_subject_grade.Subject.SubjectCode,
                    "Teacher": teacher_name if teacher_name else "N/A",
                    "SecCode": f"{student_class_subject_grade.Course.CourseCode} {student_class_subject_grade.Metadata.Year}-{student_class_subject_grade.Class.Section}",
                    "Units": format(student_class_subject_grade.Subject.Units, '.2f'),
                    "Status": checkStatus(student_class_subject_grade.StudentClassSubjectGrade.Grade) if student_class_subject_grade.StudentClassSubjectGrade.Grade is not None else "-"
                        
                }

                dict_class_group["Subject"].append(subject_details)
            return (list_student_class_subject_grade)

        else:
            return None
    except Exception as e:
        print("ERRIR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None


def getStudentData(student_id):
    try:
        print("HERE IN GETTING")
        data_student = (
            db.session.query(Student).filter(
                Student.StudentId == student_id).first()
        )
        print("data_student: ", data_student)
        if data_student:
            #  data_course_enrolled = (
            #     db.session.query(Course, CourseEnrolled)
            #     .join(CourseEnrolled, CourseEnrolled.CourseId == Course.CourseId)
            #     .filter(CourseEnrolled.StudentId==student_id)
            #     .order_by(desc(CourseEnrolled.DateEnrolled)).first()
            # )
  
            dict_student_data = {
                "StudentNumber": data_student.StudentNumber,
                "Name": data_student.Name,
                "PlaceOfBirth": data_student.PlaceOfBirth,
                "ResidentialAddress": data_student.ResidentialAddress,
                "Email": data_student.Email,
                "MobileNumber": data_student.MobileNumber,
                "Gender": "Male" if data_student.Gender == 1 else "Female",
                # "Course": data_course_enrolled.Course.CourseCode if data_course_enrolled else "None"
            }
            print('dict_student_data: ', dict_student_data)
            return (dict_student_data)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def updateStudentData(str_student_id, email, number, residentialAddress):
    try:
        if not re.match(r'^[\w\.-]+@[\w\.-]+$', email):
            return {"type": "email", "status": 400}

        if not re.match(r'^09\d{9}$', number):
            return {"type": "mobile", "status": 400}

        if residentialAddress is None or residentialAddress.strip() == "":
            return {"type": "residential", "status": 400}

        # Update the student data in the database
        data_student = db.session.query(Student).filter(
            Student.StudentId == str_student_id).first()
        
        if data_student:
            data_student.Email = email
            data_student.MobileNumber = number
            data_student.ResidentialAddress = residentialAddress
            db.session.commit()
                        
            return {"message": "Data updated successfully", "email": email, "number": number, "residentialAddress": residentialAddress, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}


def updatePassword(str_student_id, password, new_password, confirm_password):
    try:
        data_student = db.session.query(Student).filter(
            Student.StudentId == str_student_id).first()

        if data_student:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_student.Password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(
                    new_password)
                data_student.Password = new_hashed_password
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
