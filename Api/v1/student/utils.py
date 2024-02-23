from models import StudentClassGrade, Class, CourseEnrolled, CourseGrade, StudentClassSubjectGrade, Subject, ClassSubject, Class, Faculty, Student, Course, Metadata, db, LatestBatchSemester

from sqlalchemy import desc, func
from collections import defaultdict
import re
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session, jsonify

from static.js.utils import convertGradeToPercentage, checkStatus

def saveSessionValues(user_id, token):
    # Create a dictionary with all session values
    session_values = {
        'user_id': user_id,
        'user_role': 'student',
        'access_token': token['access_token'],
        'refresh_token': token['refresh_token'],
        'expires_in': token['expires_in'],
        'token_type': token['token_type'],
        'scope': token['scope'],
        'access_token_revoked_at': token['access_token_revoked_at'],
        'refresh_token_revoked_at': token['refresh_token_revoked_at'],
    }

    # Update the session with the dictionary values
    session.update(session_values)
    return None



def getCurrentUser():
    current_user_id = session.get('user_id')
    return Student.query.get(current_user_id)


def getStudentGpa(studentId):
    try:
        gpa = StudentClassGrade.query.filter_by(
            StudentId=studentId).join(Class, StudentClassGrade.ClassId == Class.ClassId).join(Metadata, Metadata.MetadataId == Class.MetadataId).filter(Class.IsGradeFinalized == True).order_by(desc(Metadata.Batch), desc(Metadata.Semester)).first()
        
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
            .filter(StudentClassGrade.StudentId == str_student_id, StudentClassGrade.Grade != None)
            .order_by(desc(Metadata.Batch), desc(Metadata.Semester))
            .all()
        )
        
        if list_student_performance:
            list_performance_data = []  # Initialize a list to store dictionary data
            for gpa in list_student_performance:
                if gpa.StudentClassGrade.Grade != None or gpa.StudentClassGrade.Grade != 0:
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
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None

def getLatestSubjectGrade(str_student_id):
    try:
        data_latest_class_subject = (
            db.session.query(StudentClassSubjectGrade, ClassSubject, Class, Metadata)
            .join(ClassSubject, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Class, ClassSubject.ClassId == Class.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .filter(StudentClassSubjectGrade.StudentId == str_student_id, Class.IsGradeFinalized == False)
            .order_by(desc(Metadata.Batch), desc(Metadata.Semester))
            .first()
        )
        
        
        if data_latest_class_subject:

            data_class_subject_grade = (
                db.session.query(ClassSubject, StudentClassSubjectGrade, Class, Metadata, Subject)
                .join(StudentClassSubjectGrade, ClassSubject.ClassSubjectId == StudentClassSubjectGrade.ClassSubjectId)
                .join(Class, Class.ClassId == ClassSubject.ClassId)
                .join(Metadata, Metadata.MetadataId == Class.MetadataId)
                .join(Subject, ClassSubject.SubjectId == Subject.SubjectId)
                .filter(StudentClassSubjectGrade.StudentId == str_student_id, ClassSubject.ClassId == data_latest_class_subject.Class.ClassId, Metadata.Semester == data_latest_class_subject.Metadata.Semester).all()
                # .all()
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

def getCoursePerformance():
    try:
        data_course_grade = db.session.query(
            Course.CourseId,
            Course.CourseCode,
            CourseGrade.Batch,
            func.avg(CourseGrade.Grade).label('average_grade')
        ).join(
            Course, Course.CourseId == CourseGrade.CourseId
        ).group_by(
            Course.CourseId, CourseGrade.Batch
        ).order_by(
            CourseGrade.Batch, Course.CourseId
        ).all()

        list_course = []

        if data_course_grade:
            course_year_grades = defaultdict(dict)

            for course_grade in data_course_grade:
                course_code = course_grade.CourseCode
                year = course_grade.Batch
                course_id = course_grade.CourseId
                
                # Check if course_code is not in list_course
                if course_code not in list_course:
                    list_course.append(course_code)

                grade = round(convertGradeToPercentage(course_grade.average_grade), 2)

                if year not in course_year_grades:
                    course_year_grades[year] = {"x": year}

                course_year_grades[year][course_code] = grade

            # Convert the data into a list of dictionaries
            formatted_data = list(course_year_grades.values())
            return jsonify({'success': True, 'list_course': list_course, 'course_performance': formatted_data})
        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return e



def getOverallGrade(str_student_id):
    try:
        data_overall_class_grade = StudentClassGrade.query.filter_by(
            StudentId=str_student_id).all()

        if data_overall_class_grade:
            total_grade = 0
            grade_count = 0

            for overall_class_grade in data_overall_class_grade:
                if isinstance(overall_class_grade.Grade, float) or isinstance(overall_class_grade.Grade, int):
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
    

def getUnitsTaken(str_student_id):
    try:
        # Get the latest batch semester where IsEnrollmentStarted is True and IsGradeFinalized is False
        data_latest_batch_semester = db.session.query(LatestBatchSemester).filter_by(IsEnrollmentStarted = True, IsGradeFinalized = False).order_by(desc(LatestBatchSemester.created_at)).first()
        
        # Get all class subject of student in which Subject.Units is sum
        data_student_class_subject = (
            db.session.query(
                StudentClassSubjectGrade.StudentId,
                func.sum(Subject.Units).label('total_units')
            )
            .join(ClassSubject, StudentClassSubjectGrade.ClassSubjectId == ClassSubject.ClassSubjectId)
            .join(Class, ClassSubject.ClassId == Class.ClassId)
            .join(Metadata, Metadata.MetadataId == Class.MetadataId)
            .join(Subject, ClassSubject.SubjectId == Subject.SubjectId)
            .filter(
                StudentClassSubjectGrade.StudentId == str_student_id,
                Metadata.Batch == data_latest_batch_semester.Batch,
                Metadata.Semester == data_latest_batch_semester.Semester
            )
            .group_by(StudentClassSubjectGrade.StudentId)
            .first()
        )
        
        print('data_student_class_subject: ', data_student_class_subject)

        if data_student_class_subject:
            
            dict_total_average_grade = {"Units": data_student_class_subject.total_units}
            
            return (dict_total_average_grade)

        else:
            return None
    except Exception as e:
        print("ERROR: ", e)
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
                if student_class_subject_grade.ClassSubject.FacultyId:
                    # Query the teacher
                    data_teacher = (
                        db.session.query(Faculty)
                        .filter(Faculty.FacultyId == student_class_subject_grade.ClassSubject.FacultyId)
                        .first()
                    )
                    teacher_name = data_teacher.LastName + ', ' + data_teacher.FirstName + ' ', data_teacher.MiddleName
                
                
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
        print("ERROR: ", e)
        # Handle the exception here, e.g., log it or return an error response
        return None


def getStudentData(student_id):
    try:
        data_student = (
            db.session.query(Student).filter(
                Student.StudentId == student_id).first()
        )
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
            return (dict_student_data)
        else:
            return None
    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        return None


def updateStudentData(str_student_id, number, residentialAddress):
    try:

        if not re.match(r'^09\d{9}$', number):
            return {"type": "mobile", "status": 400}

        if residentialAddress is None or residentialAddress.strip() == "":
            return {"type": "residential", "status": 400}

        # Update the student data in the database
        data_student = db.session.query(Student).filter(
            Student.StudentId == str_student_id).first()
        
        if data_student:
            data_student.MobileNumber = number
            data_student.ResidentialAddress = residentialAddress
            db.session.commit()
                        
            return {"message": "Data updated successfully", "number": number, "residentialAddress": residentialAddress, "status": 200}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}


def updatePassword(str_student_id, password, new_password, confirm_password):
    try:
        data_student = db.session.query(Student).filter(Student.StudentId == str_student_id).first()

  
        password_validator = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$'

        error = False
        errorList = []
        if not password:
            error = True
            errorList.append({'type': 'current_password', 'message': "Password must not be invalid"})
        elif len(password) < 8:
            error = True
            errorList.append({'type': 'current_password', 'message': "Password must be 8 characters long"})
        elif not re.match(password_validator, password):
            error = True
            errorList.append({'type': 'current_password', 'message': "Password must contain a number and characters uppercase and lowercase"})

        if not new_password:
            error = True
            errorList.append({'type': 'new_password', 'message': "New Password must not be invalid"})
        elif len(new_password) < 8:
            error = True
            errorList.append({'type': 'new_password', 'message': "New Password must be 8 characters long"})
        elif not re.match(password_validator, new_password):
            error = True
            errorList.append({'type': 'new_password', 'message': "New Password must contain a number and characters uppercase and lowercase"})

        if not confirm_password:
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must not be invalid"})
        elif len(confirm_password) < 8:
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must be 8 characters long"})
        elif not re.match(password_validator, confirm_password):
            error = True
            errorList.append({'type': 'confirm_password', 'message': "Confirm Password must contain a number and characters uppercase and lowercase"})

        if error:
            return {"error": True, 'errorList': errorList, "status": 400}
            
        
        if data_student:
            # Assuming 'password' is the hashed password stored in the database
            hashed_password = data_student.Password

            if check_password_hash(hashed_password, password):
                # If the current password matches
                new_hashed_password = generate_password_hash(new_password)
                data_student.Password = new_hashed_password
                db.session.commit()
                return {"message": "Password changed successfully", "status": 200}

            else:
                return {"message": "Changing Password was unsuccessful. Please try again.", "status": 401}
        else:
            return {"message": "Something went wrong", "status": 404}

    except Exception as e:
        # Handle the exception here, e.g., log it or return an error response
        db.session.rollback()  # Rollback the transaction in case of an error
        return {"message": "An error occurred", "status": 500}
